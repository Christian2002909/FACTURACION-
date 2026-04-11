from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, func
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class Caja(Base):
    __tablename__ = "caja"

    caj_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    caj_fecha = Column(Date, default=date.today, unique=True)
    caj_usuario = Column(String(50), nullable=False)

    # Ingresos
    caj_ventasefe = Column(Float, default=0.0)  # Ventas en efectivo
    caj_ventasche = Column(Float, default=0.0)  # Ventas con cheque
    caj_cobrosdeu = Column(Float, default=0.0)  # Cobros de deudores
    caj_adelanto = Column(Float, default=0.0)  # Adelantos de clientes
    caj_otros_ing = Column(Float, default=0.0)  # Otros ingresos

    # Egresos
    caj_compras = Column(Float, default=0.0)  # Compras
    caj_pagoprov = Column(Float, default=0.0)  # Pagos a proveedores
    caj_gastos = Column(Float, default=0.0)  # Gastos operacionales
    caj_devoluc = Column(Float, default=0.0)  # Devoluciones
    caj_otros_egr = Column(Float, default=0.0)  # Otros egresos

    # Totales
    caj_saldoinicial = Column(Float, default=0.0)
    caj_totalingre = Column(Float, default=0.0)
    caj_totalegre = Column(Float, default=0.0)
    caj_saldofinal = Column(Float, default=0.0)

    caj_cerrada = Column(Boolean, default=False)
    caj_fecha_cierre = Column(DateTime)
    caj_observacion = Column(String(255))
    caj_activo = Column(Boolean, default=True)


class MovimientoCaja(Base):
    __tablename__ = "movimiento_caja"

    mov_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mov_fecha = Column(DateTime, default=datetime.utcnow)
    mov_caja = Column(Integer, nullable=False)  # Número de caja
    mov_tipo = Column(String(20), nullable=False)  # ingreso, egreso
    mov_concepto = Column(String(100), nullable=False)  # venta, compra, gasto, etc
    mov_documento = Column(String(50))  # Número de documento asociado
    mov_monto = Column(Float, nullable=False)
    mov_observacion = Column(String(255))
    mov_usuario = Column(String(50))
    mov_activo = Column(Boolean, default=True)
