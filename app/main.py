from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, clientes, productos, facturas, pagos
from app.routers import proveedores, compras, caja, reportes
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sistema de Facturación Paraguay",
    version="1.0.0",
    description="Facturación electrónica y autoimpresa — Paraguay",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(clientes.router, prefix=PREFIX)
app.include_router(productos.router, prefix=PREFIX)
app.include_router(facturas.router, prefix=PREFIX)
app.include_router(pagos.router, prefix=PREFIX)
app.include_router(proveedores.router)
app.include_router(compras.router)
app.include_router(caja.router)
app.include_router(reportes.router)


@app.get("/")
def root():
    return {"status": "ok", "app": "Sistema de Facturación Paraguay"}
