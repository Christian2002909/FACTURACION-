from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.models.pago import MedioPago


class PagoCreate(BaseModel):
    """Datos para registrar un pago asociado a una factura."""
    factura_id: int = Field(..., gt=0, description="ID de la factura (debe ser > 0)")
    fecha_pago: date = Field(..., description="Fecha del pago")
    monto: Decimal = Field(
        ..., gt=Decimal("0"),
        description="Monto del pago (debe ser > 0)"
    )
    medio_pago: MedioPago = Field(
        default=MedioPago.EFECTIVO,
        description="Medio: EFECTIVO, TRANSFERENCIA, CHEQUE, TARJETA, OTRO"
    )
    referencia: str | None = Field(default=None, max_length=255)
    observacion: str | None = Field(default=None, max_length=500)

    @field_validator("fecha_pago")
    @classmethod
    def fecha_no_futura(cls, v):
        if v > date.today():
            raise ValueError("La fecha de pago no puede ser futura")
        return v


class PagoResponse(PagoCreate):
    id: int

    model_config = {"from_attributes": True}
