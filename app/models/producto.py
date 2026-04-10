from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class TasaIVA(str, enum.Enum):
    EXENTO = "0"
    CINCO = "5"
    DIEZ = "10"


class Producto(Base):
    __tablename__ = "producto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tasa_iva: Mapped[TasaIVA] = mapped_column(Enum(TasaIVA), nullable=False, default=TasaIVA.DIEZ)
    unidad_medida: Mapped[str] = mapped_column(String(50), default="UNIDAD")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
