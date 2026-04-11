from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from datetime import datetime, date
from app.database import Base

class Cheque(Base):
    __tablename__ = "cheque"

    che_nro = Column(Integer, primary_key=True, index=True, autoincrement=True)
    che_numero = Column(String(50), unique=True, nullable=False)  # Número de cheque
    che_fecha = Column(Date, default=date.today)
    che_fecha_venc = Column(Date, nullable=False)
    che_librador = Column(String(100))  # Persona/empresa que emite
    che_banco = Column(String(100))
    che_cuenta = Column(String(50))
    che_monto = Column(Float, nullable=False)
    che_tipo = Column(String(20), default="recibido")  # recibido, emitido
    che_estado = Column(String(20), default="activo")  # activo, depositado, devuelto, cancelado
    che_conceptonro = Column(String(50))  # Número de venta/compra asociada
    che_usuario = Column(String(50))
    che_fecha_deposito = Column(Date)
    che_observacion = Column(String(255))
    che_activo = Column(Boolean, default=True)
