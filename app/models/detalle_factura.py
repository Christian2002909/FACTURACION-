from sqlalchemy import Integer, String, Numeric, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.producto import TasaIVA


class DetalleFactura(Base):
    __tablename__ = "detalle_factura"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factura_id: Mapped[int] = mapped_column(Integer, ForeignKey("factura.id", ondelete="CASCADE"), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    producto_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("producto.id"))
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    descuento_porcentaje: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    descuento_monto: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    tasa_iva: Mapped[TasaIVA] = mapped_column(Enum(TasaIVA), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    monto_iva: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    total_linea: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    factura: Mapped["Factura"] = relationship("Factura", back_populates="detalles")
    producto: Mapped["Producto | None"] = relationship("Producto")
