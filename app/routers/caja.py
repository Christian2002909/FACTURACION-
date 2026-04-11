from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.dependencies import get_db
from app.models.caja import Caja, MovimientoCaja
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/caja", tags=["caja"])


class AbrirCajaIn(BaseModel):
    caj_usuario: str
    caj_saldoinicial: float = 0.0


class CerrarCajaIn(BaseModel):
    caj_observacion: Optional[str] = None


class MovimientoIn(BaseModel):
    mov_tipo: str  # ingreso, egreso
    mov_concepto: str
    mov_documento: Optional[str] = None
    mov_monto: float
    mov_observacion: Optional[str] = None
    mov_usuario: Optional[str] = None


class CajaOut(BaseModel):
    caj_nro: int
    caj_fecha: date
    caj_usuario: str
    caj_saldoinicial: float
    caj_totalingre: float
    caj_totalegre: float
    caj_saldofinal: float
    caj_cerrada: bool

    class Config:
        from_attributes = True


@router.get("/hoy", response_model=CajaOut)
def caja_hoy(db: Session = Depends(get_db)):
    caja = db.query(Caja).filter(Caja.caj_fecha == date.today()).first()
    if not caja:
        raise HTTPException(404, "No hay caja abierta hoy")
    return caja


@router.post("/abrir", response_model=CajaOut)
def abrir_caja(data: AbrirCajaIn, db: Session = Depends(get_db)):
    existe = db.query(Caja).filter(Caja.caj_fecha == date.today()).first()
    if existe:
        raise HTTPException(400, "Ya existe una caja para hoy")
    caja = Caja(
        caj_usuario=data.caj_usuario,
        caj_saldoinicial=data.caj_saldoinicial,
        caj_saldofinal=data.caj_saldoinicial
    )
    db.add(caja)
    db.commit()
    db.refresh(caja)
    return caja


@router.post("/cerrar")
def cerrar_caja(data: CerrarCajaIn, db: Session = Depends(get_db)):
    caja = db.query(Caja).filter(Caja.caj_fecha == date.today()).first()
    if not caja:
        raise HTTPException(404, "No hay caja abierta hoy")
    if caja.caj_cerrada:
        raise HTTPException(400, "La caja ya está cerrada")

    caja.caj_saldofinal = caja.caj_saldoinicial + caja.caj_totalingre - caja.caj_totalegre
    caja.caj_cerrada = True
    caja.caj_fecha_cierre = datetime.utcnow()
    caja.caj_observacion = data.caj_observacion
    db.commit()
    return {"ok": True, "saldo_final": caja.caj_saldofinal}


@router.post("/movimiento")
def registrar_movimiento(data: MovimientoIn, db: Session = Depends(get_db)):
    caja = db.query(Caja).filter(Caja.caj_fecha == date.today()).first()
    if not caja:
        raise HTTPException(404, "No hay caja abierta hoy. Abra la caja primero.")
    if caja.caj_cerrada:
        raise HTTPException(400, "La caja está cerrada")

    mov = MovimientoCaja(
        mov_caja=caja.caj_nro,
        mov_tipo=data.mov_tipo,
        mov_concepto=data.mov_concepto,
        mov_documento=data.mov_documento,
        mov_monto=data.mov_monto,
        mov_observacion=data.mov_observacion,
        mov_usuario=data.mov_usuario
    )

    if data.mov_tipo == "ingreso":
        caja.caj_totalingre = round(caja.caj_totalingre + data.mov_monto, 2)
    else:
        caja.caj_totalegre = round(caja.caj_totalegre + data.mov_monto, 2)

    caja.caj_saldofinal = round(
        caja.caj_saldoinicial + caja.caj_totalingre - caja.caj_totalegre, 2
    )

    db.add(mov)
    db.commit()
    return {"ok": True, "saldo_actual": caja.caj_saldofinal}


@router.get("/historial")
def historial(limit: int = 30, db: Session = Depends(get_db)):
    cajas = db.query(Caja).order_by(Caja.caj_fecha.desc()).limit(limit).all()
    return cajas
