from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.models.factura import TipoDocumento, EstadoFactura, CondicionVenta, EstadoSIFEN
from app.models.producto import TasaIVA


class DetalleFacturaCreate(BaseModel):
    """Línea de detalle para crear/actualizar una factura."""
    orden: int = Field(default=1, ge=1, description="Orden de la línea (>= 1)")
    producto_id: int | None = Field(default=None, description="ID del producto (opcional)")
    descripcion: str = Field(
        ..., min_length=1, max_length=500,
        description="Descripción del producto o servicio"
    )
    cantidad: Decimal = Field(
        ..., gt=Decimal("0"),
        description="Cantidad (debe ser mayor a 0)"
    )
    precio_unitario: Decimal = Field(
        ..., gt=Decimal("0"),
        description="Precio unitario IVA incluido (debe ser mayor a 0)"
    )
    descuento_porcentaje: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), le=Decimal("100"),
        description="Descuento en porcentaje (0-100)"
    )
    tasa_iva: TasaIVA = Field(..., description="Tasa de IVA: 0 (exenta), 5 o 10")


class DetalleFacturaResponse(DetalleFacturaCreate):
    id: int
    descuento_monto: Decimal
    subtotal: Decimal
    monto_iva: Decimal
    total_linea: Decimal

    model_config = {"from_attributes": True}


class FacturaCreate(BaseModel):
    """Datos para crear una nueva factura en estado BORRADOR."""
    tipo_documento: TipoDocumento = Field(
        default=TipoDocumento.FACTURA,
        description="Tipo: FACTURA, NOTA_CREDITO, NOTA_DEBITO, AUTOFACTURA"
    )
    fecha_emision: date = Field(..., description="Fecha de emisión (no puede ser futura)")
    cliente_id: int = Field(..., gt=0, description="ID del cliente (debe ser > 0)")
    condicion_venta: CondicionVenta = Field(
        default=CondicionVenta.CONTADO,
        description="Condición: CONTADO o CREDITO"
    )
    observacion: str | None = Field(default=None, max_length=1000)
    factura_referencia_id: int | None = Field(
        default=None,
        description="ID de factura de referencia (para NC/ND)"
    )
    detalles: list[DetalleFacturaCreate] = Field(
        ..., min_length=1,
        description="Líneas de detalle (mínimo 1)"
    )

    @field_validator("fecha_emision")
    @classmethod
    def fecha_no_futura(cls, v):
        if v > date.today():
            raise ValueError("La fecha de emisión no puede ser futura")
        return v


class FacturaUpdate(BaseModel):
    """Datos para actualizar una factura en estado BORRADOR."""
    fecha_emision: date | None = None
    condicion_venta: CondicionVenta | None = None
    observacion: str | None = Field(default=None, max_length=1000)
    detalles: list[DetalleFacturaCreate] | None = None

    @field_validator("fecha_emision")
    @classmethod
    def fecha_no_futura(cls, v):
        if v is not None and v > date.today():
            raise ValueError("La fecha de emisión no puede ser futura")
        return v


class FacturaResponse(BaseModel):
    id: int
    tipo_documento: TipoDocumento
    estado: EstadoFactura
    numero_completo: str | None
    fecha_emision: date
    cliente_id: int
    condicion_venta: CondicionVenta
    subtotal_exenta: Decimal
    subtotal_gravada_5: Decimal
    subtotal_gravada_10: Decimal
    iva_5: Decimal
    iva_10: Decimal
    total_iva: Decimal
    total: Decimal
    observacion: str | None
    sifen_cdc: str | None
    sifen_estado: EstadoSIFEN | None
    detalles: list[DetalleFacturaResponse] = []

    model_config = {"from_attributes": True}
