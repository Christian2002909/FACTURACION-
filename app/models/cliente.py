from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class TipoContribuyente(str, enum.Enum):
    RUC = "RUC"
    CI = "CI"
    PASAPORTE = "PASAPORTE"
    EXTRANJERO = "EXTRANJERO"


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = (Index("ix_cliente_ruc_ci", "ruc_ci"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_contribuyente: Mapped[TipoContribuyente] = mapped_column(Enum(TipoContribuyente), nullable=False)
    ruc_ci: Mapped[str | None] = mapped_column(String(20))
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_fantasia: Mapped[str | None] = mapped_column(String(255))
    direccion: Mapped[str | None] = mapped_column(String(500))
    ciudad: Mapped[str | None] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    facturas: Mapped[list["Factura"]] = relationship("Factura", back_populates="cliente")
