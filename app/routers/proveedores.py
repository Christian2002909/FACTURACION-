from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.dependencies import get_db
from app.models.proveedor import Proveedor
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/proveedores", tags=["proveedores"])


class ProveedorCreate(BaseModel):
    prov_ruc: str
    prov_nom: str
    prov_dir: Optional[str] = None
    prov_tel: Optional[str] = None
    prov_email: Optional[str] = None
    prov_contacto: Optional[str] = None
    prov_limite: float = 0.0


class ProveedorOut(ProveedorCreate):
    prov_cod: int
    prov_sal: float
    prov_activo: bool
    prov_fecha_reg: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProveedorOut])
def listar(activo: bool = True, db: Session = Depends(get_db)):
    return db.query(Proveedor).filter(Proveedor.prov_activo == activo).all()


@router.post("", response_model=ProveedorOut)
def crear(data: ProveedorCreate, db: Session = Depends(get_db)):
    if db.query(Proveedor).filter(Proveedor.prov_ruc == data.prov_ruc).first():
        raise HTTPException(400, "RUC ya registrado")
    prov = Proveedor(**data.model_dump())
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov


@router.get("/buscar", response_model=List[ProveedorOut])
def buscar(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return db.query(Proveedor).filter(
        or_(Proveedor.prov_ruc.contains(q), Proveedor.prov_nom.ilike(f"%{q}%")),
        Proveedor.prov_activo == True
    ).limit(20).all()


@router.get("/{cod}", response_model=ProveedorOut)
def obtener(cod: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.prov_cod == cod).first()
    if not prov:
        raise HTTPException(404, "Proveedor no encontrado")
    return prov


@router.put("/{cod}", response_model=ProveedorOut)
def actualizar(cod: int, data: ProveedorCreate, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.prov_cod == cod).first()
    if not prov:
        raise HTTPException(404, "Proveedor no encontrado")
    for k, v in data.model_dump().items():
        setattr(prov, k, v)
    db.commit()
    db.refresh(prov)
    return prov


@router.delete("/{cod}")
def eliminar(cod: int, db: Session = Depends(get_db)):
    prov = db.query(Proveedor).filter(Proveedor.prov_cod == cod).first()
    if not prov:
        raise HTTPException(404, "Proveedor no encontrado")
    prov.prov_activo = False
    db.commit()
    return {"ok": True}
