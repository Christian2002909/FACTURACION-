"""
Fixtures compartidas para toda la suite de tests — FacturaPY
"""
import os
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker

# Configurar env ANTES de importar app (evita errores de settings)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("APP_PASSWORD_HASH", "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test.db")

from app.database import Base
from app.main import app
from app.dependencies import get_db
from app.models.empresa import Empresa
from app.models.cliente import Cliente, TipoContribuyente
from app.models.producto import Producto
from app.models.enums import TasaIVA
from app.models.factura import Factura, EstadoFactura, TipoDocumento, CondicionVenta
from app.models.detalle_factura import DetalleFactura
from app.models.pago import Pago, MedioPago
from app.services.auth_service import create_access_token

# BD en memoria con StaticPool — garantiza que TODAS las conexiones
# compartan la misma BD in-memory (requisito de SQLite)
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(TEST_ENGINE, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Crea y destruye tablas para cada test."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db():
    """Sesión de BD para tests que necesitan acceso directo."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_headers():
    """Headers con token JWT válido para tests autenticados."""
    token = create_access_token({"sub": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def empresa(db):
    """Empresa de prueba con timbrado válido."""
    emp = Empresa(
        id=1,
        razon_social="Empresa Test S.A.",
        ruc="80069563-1",
        direccion="Calle Test 123",
        ciudad="Asunción",
        timbrado="12345678",
        timbrado_fecha_inicio=date.today() - timedelta(days=30),
        timbrado_fecha_fin=date.today() + timedelta(days=335),
        establecimiento="001",
        punto_expedicion="001",
        numero_actual=1,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@pytest.fixture
def cliente(db):
    """Cliente de prueba."""
    cli = Cliente(
        tipo_contribuyente=TipoContribuyente.RUC,
        ruc_ci="80069563-1",
        razon_social="Cliente Test",
        direccion="Av. Test 456",
        ciudad="Asunción",
    )
    db.add(cli)
    db.commit()
    db.refresh(cli)
    return cli


@pytest.fixture
def producto(db):
    """Producto de prueba."""
    prod = Producto(
        codigo="PROD001",
        descripcion="Producto de prueba",
        precio_unitario=110000,
        tasa_iva=TasaIVA.DIEZ,
        stock=100,
    )
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@pytest.fixture
def factura_borrador(db, cliente, empresa):
    """Factura en estado BORRADOR con 1 detalle."""
    factura = Factura(
        tipo_documento=TipoDocumento.FACTURA,
        fecha_emision=date.today(),
        cliente_id=cliente.id,
        condicion_venta=CondicionVenta.CONTADO,
        estado=EstadoFactura.BORRADOR,
        subtotal_exenta=0,
        subtotal_gravada_5=0,
        subtotal_gravada_10=100000,
        iva_5=0,
        iva_10=10000,
        total_iva=10000,
        total=110000,
    )
    db.add(factura)
    db.flush()

    detalle = DetalleFactura(
        factura_id=factura.id,
        orden=1,
        descripcion="Producto test",
        cantidad=1,
        precio_unitario=110000,
        descuento_porcentaje=0,
        descuento_monto=0,
        tasa_iva=TasaIVA.DIEZ,
        subtotal=100000,
        monto_iva=10000,
        total_linea=110000,
    )
    db.add(detalle)
    db.commit()
    db.refresh(factura)
    return factura
