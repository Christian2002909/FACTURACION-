from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.producto import TasaIVA


class ProductoBase(BaseModel):
    """Datos base de un producto o servicio."""
    codigo: str = Field(
        ..., min_length=1, max_length=50,
        description="Código único del producto"
    )
    descripcion: str = Field(
        ..., min_length=1, max_length=500,
        description="Descripción del producto o servicio"
    )
    precio_unitario: Decimal = Field(
        ..., gt=Decimal("0"),
        description="Precio unitario IVA incluido (debe ser > 0)"
    )
    tasa_iva: TasaIVA = Field(
        default=TasaIVA.DIEZ,
        description="Tasa de IVA: 0, 5 o 10"
    )
    unidad_medida: str = Field(
        default="UNIDAD", min_length=1, max_length=50,
        description="Unidad de medida"
    )


class ProductoCreate(ProductoBase):
    """Datos para crear un nuevo producto."""
    pass


class ProductoUpdate(ProductoBase):
    """Datos para actualizar un producto existente."""
    pass


class ProductoResponse(ProductoBase):
    id: int
    activo: bool

    model_config = {"from_attributes": True}
