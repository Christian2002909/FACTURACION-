"""
Servicio centralizado de emisión, cálculo y anulación de facturas.
Cumple Resolución SET N° 60/2015 — Paraguay
"""
import os
import logging
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.factura import Factura, EstadoFactura, EstadoSIFEN
from app.models.empresa import Empresa
from app.models.detalle_factura import DetalleFactura, TasaIVA
from app.pdf.factura_pdf import generar_factura_pdf
from app.core.numeracion import obtener_siguiente_numero, formatear_numero_completo
from app.config import settings

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("audit")


class FaculturaServiceError(Exception):
    """Error en operación de factura"""
    pass


def calcular_totales(factura: Factura) -> Factura:
    """
    Recorre factura.detalles y calcula todos los subtotales e IVA.
    FÓRMULAS PARAGUAY:
      - IVA 10%: IVA = precio_con_iva / 11
      - IVA 5%: IVA = precio_con_iva / 21
      - IVA 0%: exenta de impuesto
    """
    subtotal_exenta = Decimal("0")
    subtotal_gravada_5 = Decimal("0")
    subtotal_gravada_10 = Decimal("0")

    for d in factura.detalles:
        total = Decimal(str(d.cantidad)) * Decimal(str(d.precio_unitario))
        d.total_linea = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if str(d.tasa_iva.value) == "0":
            subtotal_exenta += d.total_linea
        elif str(d.tasa_iva.value) == "5":
            subtotal_gravada_5 += d.total_linea
        elif str(d.tasa_iva.value) == "10":
            subtotal_gravada_10 += d.total_linea

    iva_5 = (subtotal_gravada_5 / Decimal("21")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva_10 = (subtotal_gravada_10 / Decimal("11")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    factura.subtotal_exenta = subtotal_exenta
    factura.subtotal_gravada_5 = subtotal_gravada_5
    factura.subtotal_gravada_10 = subtotal_gravada_10
    factura.iva_5 = iva_5
    factura.iva_10 = iva_10
    factura.total_iva = iva_5 + iva_10
    factura.total = subtotal_exenta + subtotal_gravada_5 + subtotal_gravada_10 + factura.iva_5 + factura.iva_10

    return factura


def emitir_factura(db: Session, factura_id: int) -> Factura:
    """
    Cambia estado BORRADOR → EMITIDA, asigna número correlativo,
    genera PDF y opcionalmente dispara SIFEN.

    Raises:
        FaculturaServiceError: Si hay error en emisión
    """
    logger.info("Iniciando emisión de factura %d", factura_id)

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        logger.warning("Factura %d no encontrada", factura_id)
        raise FaculturaServiceError(f"Factura {factura_id} no encontrada")

    if factura.estado != EstadoFactura.BORRADOR:
        logger.warning("Intento de emitir factura %d en estado %s", factura_id, factura.estado)
        raise FaculturaServiceError(
            f"Solo se pueden emitir facturas en estado BORRADOR. "
            f"Estado actual: {factura.estado}"
        )

    empresa = db.query(Empresa).first()
    if not empresa:
        logger.error("No hay empresa configurada en el sistema")
        raise FaculturaServiceError("No hay empresa configurada en el sistema")

    # Calcular totales
    factura = calcular_totales(factura)

    # Asignar número correlativo ATÓMICO (con lock de fila via with_for_update)
    timbrado, establecimiento, punto_expedicion, numero_str = obtener_siguiente_numero(db)
    factura.timbrado = timbrado
    factura.establecimiento = establecimiento
    factura.punto_expedicion = punto_expedicion
    factura.numero = numero_str
    factura.numero_completo = formatear_numero_completo(establecimiento, punto_expedicion, numero_str)

    # Cambiar estado
    factura.estado = EstadoFactura.EMITIDA

    # Generar PDF en disco
    pdf_dir = settings.PDF_OUTPUT_DIR
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_bytes = generar_factura_pdf(factura, empresa)
    pdf_path = os.path.join(pdf_dir, f"{factura.numero_completo}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    factura.pdf_path = pdf_path

    db.commit()
    db.refresh(factura)

    # Registro de auditoría
    audit_logger.info(
        "FACTURA_EMITIDA id=%d numero=%s total=%s cliente_id=%d",
        factura.id, factura.numero_completo, factura.total, factura.cliente_id,
    )
    logger.info("Factura %d emitida: %s", factura.id, factura.numero_completo)

    # Disparar SIFEN si está habilitado (Fase 3)
    if getattr(settings, 'SIFEN_ENABLED', False):
        try:
            from app.sifen.events import on_factura_emitida
            on_factura_emitida(factura.id)
        except Exception as e:
            # SIFEN falla en silencio: la factura autoimpresa ya quedó emitida
            logger.warning("SIFEN error en factura %d: %s", factura.id, e)

    return factura


def anular_factura(db: Session, factura_id: int, motivo: str = "") -> Factura:
    """
    Anula una factura emitida. No se puede anular una electrónica aprobada
    directamente (requiere nota de crédito).

    Raises:
        FaculturaServiceError: Si hay error en anulación
    """
    logger.info("Iniciando anulación de factura %d", factura_id)

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        logger.warning("Factura %d no encontrada para anulación", factura_id)
        raise FaculturaServiceError("Factura no encontrada")

    if factura.estado != EstadoFactura.EMITIDA:
        logger.warning("Intento de anular factura %d en estado %s", factura_id, factura.estado)
        raise FaculturaServiceError("Solo se pueden anular facturas emitidas")

    if factura.sifen_estado == EstadoSIFEN.APROBADO:
        logger.warning("Intento de anular factura %d aprobada en SIFEN", factura_id)
        raise FaculturaServiceError(
            "No se puede anular una factura electrónica aprobada por SIFEN. "
            "Debe emitir una Nota de Crédito Electrónica."
        )

    factura.estado = EstadoFactura.ANULADA
    factura.observacion = motivo or "Anulada"

    # Regenerar PDF con marca de agua ANULADA
    empresa = db.query(Empresa).first()
    if empresa:
        pdf_bytes = generar_factura_pdf(factura, empresa)
        if factura.pdf_path:
            with open(factura.pdf_path, "wb") as f:
                f.write(pdf_bytes)

    db.commit()
    db.refresh(factura)

    audit_logger.info(
        "FACTURA_ANULADA id=%d numero=%s motivo=%s",
        factura.id, factura.numero_completo, motivo,
    )
    logger.info("Factura %d anulada", factura.id)

    return factura
