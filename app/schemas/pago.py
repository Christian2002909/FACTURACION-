from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from app.models.pago import MedioPago


class PagoCreate(BaseModel):
    factura_id: int
    fecha_pago: date
    monto: Decimal
    medio_pago: MedioPago = MedioPago.EFECTIVO
    referencia: str | None = None
    observacion: str | None = None


class PagoResponse(PagoCreate):
    id: int

    model_config = {"from_attributes": True}
