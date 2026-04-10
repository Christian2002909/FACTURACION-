from datetime import datetime, date
from sqlalchemy import Integer, String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_fantasia: Mapped[str | None] = mapped_column(String(255))
    ruc: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    direccion: Mapped[str] = mapped_column(String(500), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    actividad_economica: Mapped[str | None] = mapped_column(String(255))
    timbrado: Mapped[str] = mapped_column(String(20), nullable=False)
    timbrado_fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    timbrado_fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    establecimiento: Mapped[str] = mapped_column(String(3), nullable=False, default="001")
    punto_expedicion: Mapped[str] = mapped_column(String(3), nullable=False, default="001")
    numero_actual: Mapped[int] = mapped_column(Integer, default=1)
    logo_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
