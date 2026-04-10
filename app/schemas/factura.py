from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from app.models.factura import TipoDocumento, EstadoFactura, CondicionVenta, EstadoSIFEN
from app.models.producto import TasaIVA


class DetalleFacturaCreate(BaseModel):
    orden: int = 1
    producto_id: int | None = None
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_porcentaje: Decimal = Decimal("0")
    tasa_iva: TasaIVA


class DetalleFacturaResponse(DetalleFacturaCreate):
    id: int
    descuento_monto: Decimal
    subtotal: Decimal
    monto_iva: Decimal
    total_linea: Decimal

    model_config = {"from_attributes": True}


class FacturaCreate(BaseModel):
    tipo_documento: TipoDocumento = TipoDocumento.FACTURA
    fecha_emision: date
    cliente_id: int
    condicion_venta: CondicionVenta = CondicionVenta.CONTADO
    observacion: str | None = None
    factura_referencia_id: int | None = None
    detalles: list[DetalleFacturaCreate]


class FacturaUpdate(BaseModel):
    fecha_emision: date | None = None
    condicion_venta: CondicionVenta | None = None
    observacion: str | None = None
    detalles: list[DetalleFacturaCreate] | None = None


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
