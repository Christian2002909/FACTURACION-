from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class Cuota(Base):
    __tablename__ = "cuota"

    cuo_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cuo_factnro = Column(Integer, ForeignKey("factura.id"), nullable=False)
    cuo_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    cuo_numero = Column(Integer, nullable=False)  # Cuota 1, 2, 3...
    cuo_monto = Column(Float, nullable=False)
    cuo_fecha_venc = Column(Date, nullable=False)
    cuo_fecha_pago = Column(Date)
    cuo_pagado = Column(Boolean, default=False)
    cuo_observacion = Column(String(255))
    cuo_activo = Column(Boolean, default=True)

    # Relaciones
    factura = relationship("Factura")
    cliente = relationship("Cliente")
