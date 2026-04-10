from datetime import datetime, date
from sqlalchemy import Integer, String, Numeric, Date, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class MedioPago(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    CHEQUE = "CHEQUE"
    TARJETA = "TARJETA"
    OTRO = "OTRO"


class Pago(Base):
    __tablename__ = "pago"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factura_id: Mapped[int] = mapped_column(Integer, ForeignKey("factura.id", ondelete="CASCADE"), nullable=False)
    fecha_pago: Mapped[date] = mapped_column(Date, nullable=False)
    monto: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    medio_pago: Mapped[MedioPago] = mapped_column(Enum(MedioPago), nullable=False, default=MedioPago.EFECTIVO)
    referencia: Mapped[str | None] = mapped_column(String(255))
    observacion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    factura: Mapped["Factura"] = relationship("Factura", back_populates="pagos")
