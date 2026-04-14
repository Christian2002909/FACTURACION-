from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, clientes, productos, facturas, pagos
from app.routers import proveedores, compras, caja, reportes, configuracion
from app.dependencies import get_current_user
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FacturaPY — Sistema de Gestión Comercial",
    version="1.0.0",
    description="FacturaPY — Facturación electrónica y autoimpresa",
    lifespan=lifespan,
)

# CORS restrictivo — solo permitir orígenes de confianza
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(clientes.router, prefix=PREFIX)
app.include_router(productos.router, prefix=PREFIX)
app.include_router(facturas.router, prefix=PREFIX)
app.include_router(pagos.router, prefix=PREFIX)
app.include_router(proveedores.router, dependencies=[Depends(get_current_user)])
app.include_router(compras.router, dependencies=[Depends(get_current_user)])
app.include_router(caja.router, dependencies=[Depends(get_current_user)])
app.include_router(reportes.router, dependencies=[Depends(get_current_user)])
app.include_router(configuracion.router, prefix=PREFIX)


@app.get("/")
def root():
    return {"status": "ok", "app": "FacturaPY"}
