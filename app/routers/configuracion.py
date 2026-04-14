"""
Router de Configuración — FacturaPY
Verificación de clave admin y gestión de datos de empresa
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.empresa import Empresa
from app.config import settings

router = APIRouter(prefix="/config", tags=["Configuración"])


class AdminVerify(BaseModel):
    password: str


class EmpresaUpdate(BaseModel):
    razon_social: str | None = None
    nombre_fantasia: str | None = None
    ruc: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    telefono: str | None = None
    email: str | None = None
    actividad_economica: str | None = None
    timbrado: str | None = None
    timbrado_fecha_inicio: str | None = None
    timbrado_fecha_fin: str | None = None
    establecimiento: str | None = None
    punto_expedicion: str | None = None
    sifen_habilitado: bool | None = None
    logo_path: str | None = None


@router.post("/verify-admin")
def verify_admin(body: AdminVerify, _=Depends(get_current_user)):
    """Verifica la clave de administrador para configuración fiscal."""
    valid = body.password == settings.ADMIN_CONFIG_PASSWORD
    return {"valid": valid}


@router.get("/empresa")
def get_empresa(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Retorna datos de la empresa."""
    empresa = db.query(Empresa).first()
    if not empresa:
        return {"id": None, "message": "No hay empresa configurada"}
    return {
        "id": empresa.id,
        "razon_social": empresa.razon_social,
        "nombre_fantasia": empresa.nombre_fantasia,
        "ruc": empresa.ruc,
        "direccion": empresa.direccion,
        "ciudad": empresa.ciudad,
        "telefono": empresa.telefono,
        "email": empresa.email,
        "actividad_economica": empresa.actividad_economica,
        "timbrado": empresa.timbrado,
        "timbrado_fecha_inicio": str(empresa.timbrado_fecha_inicio) if empresa.timbrado_fecha_inicio else None,
        "timbrado_fecha_fin": str(empresa.timbrado_fecha_fin) if empresa.timbrado_fecha_fin else None,
        "establecimiento": empresa.establecimiento,
        "punto_expedicion": empresa.punto_expedicion,
        "sifen_habilitado": empresa.sifen_habilitado,
        "logo_path": empresa.logo_path,
    }


@router.put("/empresa")
def update_empresa(
    body: EmpresaUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Actualiza datos de la empresa (requiere JWT)."""
    empresa = db.query(Empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="No hay empresa configurada")

    for field_name, value in body.model_dump(exclude_none=True).items():
        if field_name in ("timbrado_fecha_inicio", "timbrado_fecha_fin"):
            from datetime import date as dt_date
            try:
                value = dt_date.fromisoformat(value)
            except (ValueError, TypeError):
                continue
        setattr(empresa, field_name, value)

    db.commit()
    db.refresh(empresa)
    return {"message": "Empresa actualizada", "id": empresa.id}
