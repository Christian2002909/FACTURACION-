from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date
from app.dependencies import get_db
from app.models.factura import Factura, EstadoFactura
from app.models.cliente import Cliente
from app.models.detalle_factura import DetalleFactura
from app.models.producto import Producto
from app.models.caja import Caja
from app.models.cuota import Cuota

router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])


@router.get("/ventas-periodo")
def ventas_periodo(
    desde: date = Query(...),
    hasta: date = Query(...),
    db: Session = Depends(get_db)
):
    facturas = db.query(Factura).filter(
        Factura.fecha_emision >= desde,
        Factura.fecha_emision <= hasta,
        Factura.estado == EstadoFactura.EMITIDA
    ).all()

    total = sum(float(f.total) for f in facturas)
    total_iva = sum(float(f.total_iva) for f in facturas)

    return {
        "desde": desde,
        "hasta": hasta,
        "cantidad_facturas": len(facturas),
        "total_ventas": round(total, 2),
        "total_iva": round(total_iva, 2),
        "total_neto": round(total - total_iva, 2)
    }


@router.get("/clientes-deudores")
def clientes_deudores(db: Session = Depends(get_db)):
    cuotas = db.query(
        Cuota.cuo_cliente,
        func.sum(Cuota.cuo_monto).label("total_deuda"),
        func.count(Cuota.cuo_nro).label("cuotas_pendientes")
    ).filter(
        Cuota.cuo_pagado == False,
        Cuota.cuo_activo == True
    ).group_by(Cuota.cuo_cliente).all()

    resultado = []
    for c in cuotas:
        cliente = db.query(Cliente).filter(Cliente.id == c.cuo_cliente).first()
        if cliente:
            resultado.append({
                "cliente_id": c.cuo_cliente,
                "nombre": cliente.razon_social,
                "ruc": cliente.ruc_ci,
                "total_deuda": float(c.total_deuda),
                "cuotas_pendientes": c.cuotas_pendientes
            })

    return sorted(resultado, key=lambda x: x["total_deuda"], reverse=True)


@router.get("/productos-mas-vendidos")
def productos_mas_vendidos(limit: int = 10, db: Session = Depends(get_db)):
    resultados = db.query(
        DetalleFactura.producto_id,
        func.sum(DetalleFactura.cantidad).label("total_vendido"),
        func.sum(DetalleFactura.subtotal).label("total_monto")
    ).join(
        Factura, DetalleFactura.factura_id == Factura.id
    ).filter(
        Factura.estado == EstadoFactura.EMITIDA
    ).group_by(
        DetalleFactura.producto_id
    ).order_by(
        func.sum(DetalleFactura.cantidad).desc()
    ).limit(limit).all()

    data = []
    for r in resultados:
        prod = db.query(Producto).filter(Producto.id == r.producto_id).first()
        if prod:
            data.append({
                "producto_id": r.producto_id,
                "descripcion": prod.descripcion,
                "codigo": prod.codigo,
                "total_vendido": float(r.total_vendido),
                "total_monto": float(r.total_monto)
            })
    return data


@router.get("/caja-diaria")
def caja_diaria(fecha: date = Query(default=date.today()), db: Session = Depends(get_db)):
    caja = db.query(Caja).filter(Caja.caj_fecha == fecha).first()
    if not caja:
        return {"mensaje": "No hay caja para esa fecha", "fecha": fecha}
    return {
        "fecha": caja.caj_fecha,
        "usuario": caja.caj_usuario,
        "saldo_inicial": caja.caj_saldoinicial,
        "total_ingresos": caja.caj_totalingre,
        "total_egresos": caja.caj_totalegre,
        "saldo_final": caja.caj_saldofinal,
        "cerrada": caja.caj_cerrada
    }


@router.get("/iva-mensual")
def iva_mensual(anio: int = Query(...), mes: int = Query(...), db: Session = Depends(get_db)):
    facturas = db.query(Factura).filter(
        func.extract("year", Factura.fecha_emision) == anio,
        func.extract("month", Factura.fecha_emision) == mes,
        Factura.estado == EstadoFactura.EMITIDA
    ).all()

    iva5 = sum(float(f.iva_5) for f in facturas if f.iva_5)
    iva10 = sum(float(f.iva_10) for f in facturas if f.iva_10)

    return {
        "anio": anio,
        "mes": mes,
        "cantidad_facturas": len(facturas),
        "iva_5_porciento": round(iva5, 2),
        "iva_10_porciento": round(iva10, 2),
        "total_iva": round(iva5 + iva10, 2)
    }
