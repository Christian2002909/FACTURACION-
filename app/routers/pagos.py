from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.pago import Pago
from app.schemas.pago import PagoCreate, PagoResponse
from app.core.exceptions import http_404

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("", response_model=list[PagoResponse])
def listar(factura_id: int | None = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Pago)
    if factura_id:
        q = q.filter(Pago.factura_id == factura_id)
    return q.all()


@router.post("", response_model=PagoResponse, status_code=201)
def crear(body: PagoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    pago = Pago(**body.model_dump())
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


@router.get("/{id}", response_model=PagoResponse)
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Pago).filter(Pago.id == id).first()
    if not p:
        raise http_404()
    return p


@router.delete("/{id}", status_code=204)
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Pago).filter(Pago.id == id).first()
    if not p:
        raise http_404()
    db.delete(p)
    db.commit()
