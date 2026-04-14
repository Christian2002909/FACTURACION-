"""
Servicio de vista previa de factura — solo para visualización antes de emitir.
NO asigna número, NO modifica el estado, NO escribe en disco.
Útil para el flujo: "revisar → confirmar → emitir".
"""
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session

from app.models.factura import Factura, EstadoFactura
from app.models.empresa import Empresa
from app.pdf.factura_pdf import generar_factura_pdf
from app.services.factura_service import FaculturaServiceError


def previsualizar_factura(db: Session, factura_id: int) -> bytes:
    """
    Genera PDF en memoria con marca BORRADOR para vista previa.
    No toca la base de datos.

    Returns:
        bytes: contenido del PDF listo para descargar o mostrar en browser.

    Raises:
        FaculturaServiceError: si la factura no existe o ya fue emitida/anulada.
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise FaculturaServiceError(f"Factura {factura_id} no encontrada")

    if factura.estado != EstadoFactura.BORRADOR:
        raise FaculturaServiceError(
            f"Solo se pueden previsualizar borradores. Estado actual: {factura.estado.value}"
        )

    empresa = db.query(Empresa).first()

    # Calcular totales en memoria SIN persistir — creamos un objeto temporal
    subtotal_exenta = Decimal("0")
    subtotal_gravada_5 = Decimal("0")
    subtotal_gravada_10 = Decimal("0")

    for d in factura.detalles:
        total = Decimal(str(d.cantidad)) * Decimal(str(d.precio_unitario))
        total_linea = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        tasa = str(d.tasa_iva.value)
        if tasa == "0":
            subtotal_exenta += total_linea
        elif tasa == "5":
            subtotal_gravada_5 += total_linea
        elif tasa == "10":
            subtotal_gravada_10 += total_linea

    iva_5 = (subtotal_gravada_5 / Decimal("21")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    iva_10 = (subtotal_gravada_10 / Decimal("11")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Parche temporal en objeto (sin commit)
    factura.subtotal_exenta = subtotal_exenta
    factura.subtotal_gravada_5 = subtotal_gravada_5
    factura.subtotal_gravada_10 = subtotal_gravada_10
    factura.iva_5 = iva_5
    factura.iva_10 = iva_10
    factura.total_iva = iva_5 + iva_10
    factura.total = subtotal_exenta + subtotal_gravada_5 + subtotal_gravada_10

    # numero_completo visual para el preview
    _numero_original = factura.numero_completo
    if empresa and not factura.numero_completo:
        est = empresa.establecimiento or "001"
        pto = empresa.punto_expedicion or "001"
        prox = str(empresa.numero_actual).zfill(7)
        factura.numero_completo = f"{est}-{pto}-{prox} [BORRADOR]"

    pdf_bytes = generar_factura_pdf(factura, empresa)

    # Restaurar — no queremos que SQLAlchemy persista estos cambios
    factura.numero_completo = _numero_original
    db.expire(factura)  # descartar cambios en memoria

    return pdf_bytes
