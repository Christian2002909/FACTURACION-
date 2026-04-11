from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.dependencies import get_db
from app.models.compra import Compra, CompraItem
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/compras", tags=["compras"])


class ItemCompraIn(BaseModel):
    citem_procod: int
    citem_cant: float
    citem_precio: float


class CompraCreate(BaseModel):
    com_proveedor: int
    com_tipo: int = 1  # 1=Contado, 2=Crédito, 3=Cheque
    com_observacion: Optional[str] = None
    items: List[ItemCompraIn]


class ItemCompraOut(BaseModel):
    citem_id: int
    citem_procod: int
    citem_cant: float
    citem_precio: float
    citem_subtotal: float

    class Config:
        from_attributes = True


class CompraOut(BaseModel):
    com_nro: int
    com_fecha: datetime
    com_proveedor: int
    com_total: float
    com_tipo: int
    com_estado: str
    com_observacion: Optional[str]
    items: List[ItemCompraOut]

    class Config:
        from_attributes = True


@router.get("", response_model=List[CompraOut])
def listar(db: Session = Depends(get_db)):
    return db.query(Compra).filter(Compra.com_activo == True).order_by(Compra.com_nro.desc()).all()


@router.post("", response_model=CompraOut)
def crear(data: CompraCreate, db: Session = Depends(get_db)):
    if not db.query(Proveedor).filter(Proveedor.prov_cod == data.com_proveedor).first():
        raise HTTPException(404, "Proveedor no encontrado")

    total = 0.0
    items_db = []
    for item in data.items:
        prod = db.query(Producto).filter(Producto.id == item.citem_procod).first()
        if not prod:
            raise HTTPException(404, f"Producto {item.citem_procod} no encontrado")
        subtotal = round(item.citem_cant * item.citem_precio, 2)
        total += subtotal
        items_db.append(CompraItem(
            citem_procod=item.citem_procod,
            citem_cant=item.citem_cant,
            citem_precio=item.citem_precio,
            citem_subtotal=subtotal
        ))
        # Actualizar stock
        prod.stock = getattr(prod, "stock", 0) + item.citem_cant

    compra = Compra(
        com_proveedor=data.com_proveedor,
        com_tipo=data.com_tipo,
        com_observacion=data.com_observacion,
        com_total=round(total, 2),
        com_estado="recibida",
        items=items_db
    )
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


@router.get("/{nro}", response_model=CompraOut)
def obtener(nro: int, db: Session = Depends(get_db)):
    c = db.query(Compra).filter(Compra.com_nro == nro).first()
    if not c:
        raise HTTPException(404, "Compra no encontrada")
    return c


@router.post("/{nro}/anular")
def anular(nro: int, db: Session = Depends(get_db)):
    c = db.query(Compra).filter(Compra.com_nro == nro).first()
    if not c:
        raise HTTPException(404, "Compra no encontrada")
    if c.com_estado == "anulada":
        raise HTTPException(400, "Compra ya anulada")
    c.com_estado = "anulada"
    c.com_activo = False
    db.commit()
    return {"ok": True}
