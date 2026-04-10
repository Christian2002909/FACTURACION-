from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from app.core.exceptions import http_404

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_model=list[ClienteResponse])
def listar(search: str | None = None, activo: bool = True, skip: int = 0, limit: int = 100,
           db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Cliente).filter(Cliente.activo == activo)
    if search:
        q = q.filter(Cliente.razon_social.ilike(f"%{search}%") | Cliente.ruc_ci.ilike(f"%{search}%"))
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=ClienteResponse, status_code=201)
def crear(body: ClienteCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = Cliente(**body.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/buscar", response_model=ClienteResponse)
def buscar_por_ruc(ruc: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.ruc_ci == ruc, Cliente.activo == True).first()
    if not cliente:
        raise http_404("Cliente no encontrado")
    return cliente


@router.get("/{id}", response_model=ClienteResponse)
def obtener(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise http_404()
    return cliente


@router.put("/{id}", response_model=ClienteResponse)
def actualizar(id: int, body: ClienteUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise http_404()
    for k, v in body.model_dump().items():
        setattr(cliente, k, v)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{id}", status_code=204)
def eliminar(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise http_404()
    cliente.activo = False
    db.commit()
