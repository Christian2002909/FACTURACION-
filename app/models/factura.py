from datetime import datetime, date
from sqlalchemy import Integer, String, Boolean, DateTime, Date, Enum, Numeric, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class TipoDocumento(str, enum.Enum):
    FACTURA = "FACTURA"
    NOTA_CREDITO = "NOTA_CREDITO"
    NOTA_DEBITO = "NOTA_DEBITO"
    AUTOFACTURA = "AUTOFACTURA"


class EstadoFactura(str, enum.Enum):
    BORRADOR = "BORRADOR"
    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"


class CondicionVenta(str, enum.Enum):
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"


class EstadoSIFEN(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ENVIADO = "ENVIADO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class Factura(Base):
    __tablename__ = "factura"
    __table_args__ = (
        UniqueConstraint("timbrado", "establecimiento", "punto_expedicion", "numero", "tipo_documento",
                         name="uq_factura_numero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento), nullable=False, default=TipoDocumento.FACTURA)
    timbrado: Mapped[str | None] = mapped_column(String(20))
    establecimiento: Mapped[str | None] = mapped_column(String(3))
    punto_expedicion: Mapped[str | None] = mapped_column(String(3))
    numero: Mapped[str | None] = mapped_column(String(7))
    numero_completo: Mapped[str | None] = mapped_column(String(20), index=True)
    fecha_emision: Mapped[date] = mapped_column(Date, nullable=False)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("cliente.id"), nullable=False)
    condicion_venta: Mapped[CondicionVenta] = mapped_column(Enum(CondicionVenta), nullable=False, default=CondicionVenta.CONTADO)
    moneda: Mapped[str] = mapped_column(String(3), default="PYG")
    subtotal_exenta: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    subtotal_gravada_5: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    subtotal_gravada_10: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    iva_5: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    iva_10: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    total_iva: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    estado: Mapped[EstadoFactura] = mapped_column(Enum(EstadoFactura), nullable=False, default=EstadoFactura.BORRADOR)
    observacion: Mapped[str | None] = mapped_column(Text)
    factura_referencia_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("factura.id"))
    sifen_cdc: Mapped[str | None] = mapped_column(String(44))
    sifen_estado: Mapped[EstadoSIFEN | None] = mapped_column(Enum(EstadoSIFEN))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="facturas")
    detalles: Mapped[list["DetalleFactura"]] = relationship("DetalleFactura", back_populates="factura", cascade="all, delete-orphan")
    pagos: Mapped[list["Pago"]] = relationship("Pago", back_populates="factura", cascade="all, delete-orphan")
    factura_referencia: Mapped["Factura | None"] = relationship("Factura", remote_side="Factura.id")
