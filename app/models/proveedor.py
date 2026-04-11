from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Proveedor(Base):
    __tablename__ = "proveedor"

    prov_cod = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prov_ruc = Column(String(20), unique=True, nullable=False, index=True)
    prov_nom = Column(String(255), nullable=False)
    prov_dir = Column(String(255))
    prov_tel = Column(String(20))
    prov_email = Column(String(100))
    prov_contacto = Column(String(100))
    prov_limite = Column(Float, default=0.0)
    prov_sal = Column(Float, default=0.0)  # Saldo actual (deuda)
    prov_activo = Column(Boolean, default=True)
    prov_fecha_reg = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    compras = relationship("Compra", back_populates="proveedor")
