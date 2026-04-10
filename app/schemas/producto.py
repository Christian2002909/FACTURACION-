from decimal import Decimal
from pydantic import BaseModel
from app.models.producto import TasaIVA


class ProductoBase(BaseModel):
    codigo: str
    descripcion: str
    precio_unitario: Decimal
    tasa_iva: TasaIVA = TasaIVA.DIEZ
    unidad_medida: str = "UNIDAD"


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(ProductoBase):
    pass


class ProductoResponse(ProductoBase):
    id: int
    activo: bool

    model_config = {"from_attributes": True}
