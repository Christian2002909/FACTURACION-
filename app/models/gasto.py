from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from datetime import datetime, date
from app.database import Base

class Gasto(Base):
    __tablename__ = "gasto"

    gas_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gas_fecha = Column(Date, default=date.today)
    gas_concepto = Column(String(100), nullable=False)  # arriendo, servicios, publicidad, etc
    gas_monto = Column(Float, nullable=False)
    gas_categoria = Column(String(50))
    gas_usuario = Column(String(50))
    gas_comprobante = Column(String(50))
    gas_observacion = Column(String(255))
    gas_activo = Column(Boolean, default=True)


class Motivo(Base):
    __tablename__ = "motivo"

    mot_cod = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mot_descri = Column(String(100), nullable=False)
    mot_tipo = Column(String(20), nullable=False)  # ajuste, devolución, etc
    mot_activo = Column(Boolean, default=True)


class Ajuste(Base):
    __tablename__ = "ajuste"

    aju_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    aju_fecha = Column(DateTime, default=datetime.utcnow)
    aju_procod = Column(Integer, ForeignKey("producto.id"), nullable=False)
    aju_cant = Column(Float, nullable=False)
    aju_motivo = Column(Integer)  # FK a motivo
    aju_usuario = Column(String(50))
    aju_observacion = Column(String(255))
    aju_activo = Column(Boolean, default=True)
