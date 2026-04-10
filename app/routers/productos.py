from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.producto import Producto
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from app.core.exceptions import http_404

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=list[ProductoResponse])
def listar(search: str | None = None, activo: bool = True, skip: int = 0, limit: int = 100,
           db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Producto).filter(Producto.activo == activo)
    if search:
        q = q.filter(Producto.descripcion.ilike(f"%{search}%") | Producto.codigo.ilike(f"%{search}%"))
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=ProductoResponse, status_code=201)
def crear(body: ProductoCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    producto = Producto(**body.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.get("/buscar", response_model=ProductoResponse)
def buscar_por_codigo(codigo: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.codigo == codigo, Producto.activo == True).first()
    if not p:
        raise http_404("Producto no encontrado")
    return p


@router.get("/{id}", response_model=ProductoResponse)
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise http_404()
    return p


@router.put("/{id}", response_model=ProductoResponse)
def actualizar(id: int, body: ProductoUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise http_404()
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{id}", status_code=204)
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.id == id).first()
    if not p:
        raise http_404()
    p.activo = False
    db.commit()
