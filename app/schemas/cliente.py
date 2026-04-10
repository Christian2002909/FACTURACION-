from pydantic import BaseModel, EmailStr, field_validator
from app.models.cliente import TipoContribuyente
from app.core.ruc_validator import validar_ruc
from app.core.exceptions import RUCInvalidoError


class ClienteBase(BaseModel):
    tipo_contribuyente: TipoContribuyente
    ruc_ci: str | None = None
    razon_social: str
    nombre_fantasia: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    telefono: str | None = None
    email: str | None = None

    @field_validator("ruc_ci")
    @classmethod
    def validar_ruc_ci(cls, v, info):
        if v and info.data.get("tipo_contribuyente") == TipoContribuyente.RUC:
            try:
                return validar_ruc(v)
            except RUCInvalidoError as e:
                raise ValueError(str(e))
        return v


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(ClienteBase):
    pass


class ClienteResponse(ClienteBase):
    id: int
    activo: bool

    model_config = {"from_attributes": True}
