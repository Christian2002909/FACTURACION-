from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Compra(Base):
    __tablename__ = "compra"

    com_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    com_fecha = Column(DateTime, default=datetime.utcnow)
    com_proveedor = Column(Integer, ForeignKey("proveedor.prov_cod"), nullable=False)
    com_total = Column(Float, default=0.0)
    com_tipo = Column(Integer, default=1)  # 1=Contado, 2=Crédito, 3=Cheque
    com_usuario = Column(String(50))  # Usuario que registró
    com_estado = Column(String(20), default="pendiente")  # pendiente, recibida, anulada
    com_observacion = Column(String(255))
    com_activo = Column(Boolean, default=True)

    # Relaciones
    proveedor = relationship("Proveedor", back_populates="compras")
    items = relationship("CompraItem", back_populates="compra", cascade="all, delete-orphan")


class CompraItem(Base):
    __tablename__ = "compra_item"

    citem_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    citem_compnro = Column(Integer, ForeignKey("compra.com_nro"), nullable=False)
    citem_procod = Column(Integer, ForeignKey("producto.id"), nullable=False)
    citem_cant = Column(Float, nullable=False)
    citem_precio = Column(Float, nullable=False)
    citem_subtotal = Column(Float, nullable=False)  # cant × precio

    # Relaciones
    compra = relationship("Compra", back_populates="items")
    producto = relationship("Producto")
