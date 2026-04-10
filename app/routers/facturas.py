from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from io import BytesIO
from app.dependencies import get_db, get_current_user
from app.models.factura import Factura, EstadoFactura
from app.models.detalle_factura import DetalleFactura
from app.schemas.factura import FacturaCreate, FacturaUpdate, FacturaResponse
from app.core.iva_calculator import calcular_iva_linea, calcular_totales
from app.core.numeracion import obtener_siguiente_numero, formatear_numero_completo
from app.core.exceptions import http_404, http_400, http_409
from app.sifen.events import on_factura_emitida

router = APIRouter(prefix="/facturas", tags=["facturas"])


def _calcular_y_crear_detalles(db, factura, detalles_data):
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


@router.get("", response_model=list[FacturaResponse])
def listar(estado: EstadoFactura | None = None, cliente_id: int | None = None,
           skip: int = 0, limit: int = 100,
           db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Factura)
    if estado:
        q = q.filter(Factura.estado == estado)
    if cliente_id:
        q = q.filter(Factura.cliente_id == cliente_id)
    return q.order_by(Factura.id.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=FacturaResponse, status_code=201)
def crear(body: FacturaCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
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


@router.get("/{id}", response_model=FacturaResponse)
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Factura).filter(Factura.id == id).first()
    if not f:
        raise http_404()
    return f


@router.put("/{id}", response_model=FacturaResponse)
def actualizar(id: int, body: FacturaUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Factura).filter(Factura.id == id).first()
    if not f:
        raise http_404()
    if f.estado != EstadoFactura.BORRADOR:
        raise http_400("Solo se pueden editar facturas en estado BORRADOR")
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


@router.post("/{id}/emitir", response_model=FacturaResponse)
def emitir(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Factura).filter(Factura.id == id).first()
    if not f:
        raise http_404()
    if f.estado != EstadoFactura.BORRADOR:
        raise http_409(f"La factura está en estado {f.estado}, no se puede emitir")
    if not f.detalles:
        raise http_400("La factura no tiene detalles")

    timbrado, establecimiento, punto, numero = obtener_siguiente_numero(db)
    f.timbrado = timbrado
    f.establecimiento = establecimiento
    f.punto_expedicion = punto
    f.numero = numero
    f.numero_completo = formatear_numero_completo(establecimiento, punto, numero)
    f.estado = EstadoFactura.EMITIDA
    db.commit()
    db.refresh(f)

    on_factura_emitida(f.id)
    return f


@router.post("/{id}/anular", response_model=FacturaResponse)
def anular(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Factura).filter(Factura.id == id).first()
    if not f:
        raise http_404()
    if f.estado != EstadoFactura.EMITIDA:
        raise http_409(f"Solo se pueden anular facturas EMITIDAS, estado actual: {f.estado}")
    f.estado = EstadoFactura.ANULADA
    db.commit()
    db.refresh(f)
    return f


@router.get("/{id}/pdf")
def generar_pdf(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    f = db.query(Factura).filter(Factura.id == id).first()
    if not f:
        raise http_404()
    from app.pdf.factura_pdf import generar_factura_pdf
    empresa = db.query(__import__("app.models.empresa", fromlist=["Empresa"]).Empresa).filter_by(id=1).first()
    pdf_bytes = generar_factura_pdf(f, empresa)
    nombre = f"factura_{f.numero_completo or f.id}.pdf"
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={nombre}"})
