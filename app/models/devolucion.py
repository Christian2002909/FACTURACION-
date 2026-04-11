from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Devolucion(Base):
    __tablename__ = "devolucion"

    dev_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dev_fecha = Column(DateTime, default=datetime.utcnow)
    dev_facturnro = Column(Integer, ForeignKey("factura.id"), nullable=False)
    dev_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    dev_motivo = Column(String(255), nullable=False)
    dev_total = Column(Float, default=0.0)
    dev_usuario = Column(String(50))
    dev_estado = Column(String(20), default="pendiente")  # pendiente, procesada, anulada
    dev_activo = Column(Boolean, default=True)

    # Relaciones
    factura = relationship("Factura")
    cliente = relationship("Cliente")
    items = relationship("DevolucionItem", back_populates="devolucion", cascade="all, delete-orphan")


class DevolucionItem(Base):
    __tablename__ = "devolucion_item"

    ditem_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ditem_devnro = Column(Integer, ForeignKey("devolucion.dev_nro"), nullable=False)
    ditem_procod = Column(Integer, ForeignKey("producto.id"), nullable=False)
    ditem_cant = Column(Float, nullable=False)
    ditem_precio = Column(Float, nullable=False)
    ditem_subtotal = Column(Float, nullable=False)

    # Relaciones
    devolucion = relationship("Devolucion", back_populates="items")
    producto = relationship("Producto")


class NotaCredito(Base):
    __tablename__ = "nota_credito"

    nc_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nc_fecha = Column(DateTime, default=datetime.utcnow)
    nc_devnro = Column(Integer, ForeignKey("devolucion.dev_nro"), nullable=False)
    nc_cliente = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    nc_monto = Column(Float, nullable=False)
    nc_estado = Column(String(20), default="emitida")  # emitida, aplicada, anulada
    nc_activo = Column(Boolean, default=True)

    # Relaciones
    cliente = relationship("Cliente")
    devolucion = relationship("Devolucion")
