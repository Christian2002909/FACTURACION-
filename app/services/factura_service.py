"""
Servicio centralizado de emisión, cálculo y anulación de facturas.
Cumple Resolución SET N° 60/2015 — Paraguay
"""
import os
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.factura import Factura, EstadoFactura, EstadoSIFEN
from app.models.empresa import Empresa
from app.models.detalle_factura import DetalleFactura, TasaIVA
from app.pdf.factura_pdf import generar_factura_pdf


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
    factura.total = subtotal_exenta + subtotal_gravada_5 + subtotal_gravada_10

    return factura


def emitir_factura(db: Session, factura_id: int) -> Factura:
    """
    Cambia estado BORRADOR → EMITIDA, asigna número correlativo,
    genera PDF y opcionalmente dispara SIFEN.

    Raises:
        FaculturaServiceError: Si hay error en emisión
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise FaculturaServiceError(f"Factura {factura_id} no encontrada")

    if factura.estado != EstadoFactura.BORRADOR:
        raise FaculturaServiceError(
            f"Solo se pueden emitir facturas en estado BORRADOR. "
            f"Estado actual: {factura.estado}"
        )

    empresa = db.query(Empresa).first()
    if not empresa:
        raise FaculturaServiceError("No hay empresa configurada en el sistema")

    # Calcular totales
    factura = calcular_totales(factura)

    # Asignar número correlativo ATÓMICO
    numero_str = str(empresa.numero_actual).zfill(7)
    factura.timbrado = empresa.timbrado
    factura.establecimiento = empresa.establecimiento
    factura.punto_expedicion = empresa.punto_expedicion
    factura.numero = numero_str
    factura.numero_completo = f"{empresa.establecimiento}-{empresa.punto_expedicion}-{numero_str}"
    empresa.numero_actual += 1

    # Cambiar estado
    factura.estado = EstadoFactura.EMITIDA

    # Generar PDF en disco
    pdf_dir = "data/facturas"
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_bytes = generar_factura_pdf(factura, empresa)
    pdf_path = os.path.join(pdf_dir, f"{factura.numero_completo}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    factura.pdf_path = pdf_path

    db.commit()
    db.refresh(factura)

    # Disparar SIFEN si está habilitado (TODO: implementar en Fase 3)
    # if settings.SIFEN_ENABLED:
    #     from app.sifen.events import on_factura_emitida
    #     on_factura_emitida(factura.id)

    return factura


def anular_factura(db: Session, factura_id: int, motivo: str = "") -> Factura:
    """
    Anula una factura emitida. No se puede anular una electrónica aprobada
    directamente (requiere nota de crédito).

    Raises:
        FaculturaServiceError: Si hay error en anulación
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise FaculturaServiceError("Factura no encontrada")

    if factura.estado != EstadoFactura.EMITIDA:
        raise FaculturaServiceError("Solo se pueden anular facturas emitidas")

    if factura.sifen_estado == EstadoSIFEN.APROBADO:
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
    return factura
