"""
Router de Facturas — Endpoints CRUD + emisión + PDF
Usa factura_service.py para lógica centralizada
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.dependencies import get_db, get_current_user
from app.models.factura import Factura, EstadoFactura
from app.models.detalle_factura import DetalleFactura
from app.models.empresa import Empresa
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaResponse
from app.core.iva_calculator import calcular_iva_linea, calcular_totales
from app.pdf.factura_pdf import generar_factura_pdf
from app.services.factura_service import emitir_factura, anular_factura, FaculturaServiceError
from app.services.preview_service import previsualizar_factura
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/facturas", tags=["Facturas"])


def _calcular_y_crear_detalles(db, factura, detalles_data):
    """Crea detalles de factura y calcula totales."""
    lineas = []
    for i, d in enumerate(detalles_data):
        total_linea = d.cantidad * d.precio_unitario * (1 - d.descuento_porcentaje / 100)
        descuento_monto = d.cantidad * d.precio_unitario * d.descuento_porcentaje / 100
        res = calcular_iva_linea(total_linea, d.tasa_iva.value)
        detalle = DetalleFactura(
            factura_id=factura.id,
            orden=d.orden if d.orden else i + 1,
            producto_id=d.producto_id,
            descripcion=d.descripcion,
            cantidad=d.cantidad,
            precio_unitario=d.precio_unitario,
            descuento_porcentaje=d.descuento_porcentaje,
            descuento_monto=descuento_monto,
            tasa_iva=d.tasa_iva,
            subtotal=res.base_imponible,
            monto_iva=res.monto_iva,
            total_linea=res.total_linea,
        )
        db.add(detalle)
        lineas.append({"total_linea": total_linea, "tasa_iva": d.tasa_iva.value})

    totales = calcular_totales(lineas)
    factura.subtotal_exenta = totales.subtotal_exenta
    factura.subtotal_gravada_5 = totales.subtotal_gravada_5
    factura.subtotal_gravada_10 = totales.subtotal_gravada_10
    factura.iva_5 = totales.iva_5
    factura.iva_10 = totales.iva_10
    factura.total_iva = totales.total_iva
    factura.total = totales.total


@router.get(
    "",
    response_model=list[FacturaResponse],
    summary="Listar facturas",
    description="Lista facturas con filtros opcionales por estado y cliente.",
)
def listar(
    estado: EstadoFactura | None = None,
    cliente_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(Factura)
    if estado:
        q = q.filter(Factura.estado == estado)
    if cliente_id:
        q = q.filter(Factura.cliente_id == cliente_id)
    return q.order_by(Factura.id.desc()).offset(skip).limit(limit).all()


@router.post(
    "",
    response_model=FacturaResponse,
    status_code=201,
    summary="Crear factura",
    description="Crea una nueva factura en estado BORRADOR. Requiere al menos 1 detalle.",
)
@limiter.limit("100/hour")
def crear(
    request: Request,
    body: FacturaCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    logger.info("Creando factura para cliente %d", body.cliente_id)
    factura = Factura(
        tipo_documento=body.tipo_documento,
        fecha_emision=body.fecha_emision,
        cliente_id=body.cliente_id,
        condicion_venta=body.condicion_venta,
        observacion=body.observacion,
        factura_referencia_id=body.factura_referencia_id,
    )
    db.add(factura)
    db.flush()
    _calcular_y_crear_detalles(db, factura, body.detalles)
    db.commit()
    db.refresh(factura)
    return factura


@router.get(
    "/{factura_id}",
    response_model=FacturaResponse,
    summary="Obtener factura",
    description="Obtiene detalle completo de una factura por ID.",
    responses={404: {"description": "Factura no encontrada"}},
)
def obtener(
    factura_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    f = db.query(Factura).filter(Factura.id == factura_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return f


@router.put(
    "/{factura_id}",
    response_model=FacturaResponse,
    summary="Actualizar factura",
    description="Actualiza una factura existente. Solo facturas en estado BORRADOR pueden editarse.",
    responses={
        400: {"description": "La factura no está en estado BORRADOR"},
        404: {"description": "Factura no encontrada"},
    },
)
def actualizar(
    factura_id: int,
    body: FacturaUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    f = db.query(Factura).filter(Factura.id == factura_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if f.estado != EstadoFactura.BORRADOR:
        raise HTTPException(status_code=400, detail="Solo se pueden editar facturas en estado BORRADOR")

    if body.fecha_emision:
        f.fecha_emision = body.fecha_emision
    if body.condicion_venta:
        f.condicion_venta = body.condicion_venta
    if body.observacion is not None:
        f.observacion = body.observacion
    if body.detalles is not None:
        for d in f.detalles:
            db.delete(d)
        db.flush()
        _calcular_y_crear_detalles(db, f, body.detalles)

    db.commit()
    db.refresh(f)
    return f


@router.post(
    "/{factura_id}/emitir",
    response_model=FacturaResponse,
    summary="Emitir factura",
    description=(
        "Emite una factura (BORRADOR → EMITIDA). "
        "Asigna número correlativo, genera PDF y dispara SIFEN si está habilitado."
    ),
    responses={
        400: {"description": "Estado inválido o empresa no configurada"},
        404: {"description": "Factura no encontrada"},
    },
)
@limiter.limit("60/hour")
def emitir(
    request: Request,
    factura_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    try:
        if not db.query(Factura).filter(Factura.id == factura_id).first():
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        return emitir_factura(db, factura_id)
    except FaculturaServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{factura_id}/anular",
    response_model=FacturaResponse,
    summary="Anular factura",
    description=(
        "Anula una factura emitida. "
        "No se puede anular si está aprobada en SIFEN (requiere Nota de Crédito). "
        "Regenera PDF con marca ANULADA."
    ),
    responses={
        400: {"description": "Estado inválido o aprobada en SIFEN"},
        404: {"description": "Factura no encontrada"},
    },
)
def anular(
    factura_id: int,
    motivo: str = "",
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    try:
        if not db.query(Factura).filter(Factura.id == factura_id).first():
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        return anular_factura(db, factura_id, motivo)
    except FaculturaServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{factura_id}/preview")
def previsualizar(
    factura_id: int,
    paper_size: str = Query("a4"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """
    Vista previa del PDF de un borrador antes de emitir.
    No asigna número, no cambia estado, no escribe en disco.
    """
    try:
        pdf_bytes = previsualizar_factura(db, factura_id, paper_size=paper_size)
    except FaculturaServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=preview_borrador_{factura_id}.pdf"}
    )


@router.get("/{factura_id}/pdf")
def descargar_pdf(
    factura_id: int,
    paper_size: str = Query("a4"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Descarga el PDF de una factura emitida."""
    f = db.query(Factura).filter(Factura.id == factura_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if f.estado == EstadoFactura.BORRADOR:
        raise HTTPException(status_code=400, detail="No se puede descargar PDF de un borrador. Primero emitir la factura.")

    # Si existe archivo en disco y se pide A4 (default), devolverlo
    if paper_size.lower() == "a4" and f.pdf_path and os.path.exists(f.pdf_path):
        return FileResponse(
            f.pdf_path,
            media_type="application/pdf",
            filename=f"factura_{f.numero_completo}.pdf"
        )

    # Generar en memoria con el tamaño solicitado
    empresa = db.query(Empresa).first()
    pdf_bytes = generar_factura_pdf(f, empresa, paper_size=paper_size)
    nombre = f"factura_{f.numero_completo or f.id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )


@router.post("/admin/activar-sifen")
def activar_sifen_empresa(
    empresa_id: int = 1,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Activa SIFEN para una empresa (solo para administrador/vendedor)."""
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    empresa.sifen_habilitado = True
    db.commit()
    db.refresh(empresa)
    return {"mensaje": "SIFEN habilitado para esta empresa", "empresa_id": empresa.id, "sifen_habilitado": empresa.sifen_habilitado}


@router.post("/{factura_id}/cancelar-de")
def cancelar_de_sifen(
    factura_id: int,
    motivo: str = "",
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Cancela un DE aprobado en SIFEN (solo si está APROBADO)."""
    from app.models.factura import EstadoSIFEN
    from app.sifen.client import cancelar_de

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if factura.sifen_estado != EstadoSIFEN.APROBADO:
        raise HTTPException(status_code=400, detail="Solo se puede cancelar un DE con estado APROBADO en SIFEN")

    if not factura.sifen_cdc:
        raise HTTPException(status_code=400, detail="La factura no tiene CDC asignado")

    empresa = db.query(Empresa).first()
    try:
        resultado = cancelar_de(factura.sifen_cdc, motivo or "Cancelación", empresa)
        factura.estado = EstadoFactura.ANULADA
        factura.observacion = f"Cancelado en SIFEN: {motivo}"
        db.commit()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
