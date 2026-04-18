# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos esenciales

```bash
# Ejecutar la aplicación completa (API + GUI)
python run.py

# Solo el servidor API (para desarrollo de endpoints)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Tests
pytest tests/                        # todos los tests
pytest tests/test_iva_calculator.py  # un test específico
pytest -v                            # con detalle

# Migraciones Alembic
alembic upgrade head                 # aplicar migraciones pendientes
alembic revision --autogenerate -m "descripción"  # nueva migración

# Build ejecutable Windows (desde Linux)
./build.sh           # genera dist/FacturaPY/FacturaPY.exe
./build.sh --nsis    # genera instalador dist/FacturaPY-setup.exe
```

El `.env` debe existir con al menos `APP_PASSWORD_HASH` y `JWT_SECRET_KEY`. Ver `app/config.py` para todas las variables.

## Arquitectura

**Stack:** FastAPI (API REST) + SQLite/SQLAlchemy + CustomTkinter (GUI de escritorio)

**Flujo de arranque (`run.py`):**
1. Auto-sync de BD: agrega columnas faltantes sin borrar datos via `PRAGMA table_info` + `ALTER TABLE`
2. Lanza `uvicorn` como subproceso
3. Espera que el servidor responda en `http://127.0.0.1:8000`
4. Instancia `App` de CustomTkinter — la GUI consume la API via HTTP local

**API (`app/`):**
- `main.py` — FastAPI app, CORS, registro de routers bajo `/api/v1`
- `routers/` — endpoints REST por entidad (auth, clientes, productos, facturas, pagos, proveedores, compras, caja, reportes, configuracion)
- `services/` — lógica de negocio: `factura_service.py` (emisión, cálculo IVA, anulación, PDF), `auth_service.py`, `preview_service.py`
- `models/` — SQLAlchemy ORM, enums, relaciones. `enums.py` centraliza los enums compartidos
- `core/` — módulos normativos: `iva_calculator.py`, `ruc_validator.py`, `numeracion.py`, `validators.py`, `exceptions.py`
- `pdf/factura_pdf.py` — generador PDF ReportLab compatible con Resolución SET N° 60/2015
- `database.py` — engine SQLite con WAL mode y foreign keys ON
- `config.py` — `Settings` via pydantic-settings, lee `.env`

**GUI (`app/gui/main_window.py`):**
Un único módulo de ~2500 líneas con toda la interfaz. Contiene: `APIClient` (singleton global `client`), funciones utilitarias, `LoginScreen`, `Sidebar`, paneles por sección (`DashboardPanel`, `ClientesPanel`, `ProductosPanel`, `FacturasPanel`, etc.), formularios modales (`ClienteForm`, `ProductoForm`, `FacturaForm`, etc.) y la clase `App` principal. Las llamadas HTTP usan `threading.Thread` + `widget.after(0, callback)` para no bloquear el hilo de UI.

## Normativa Paraguay (SET)

Este sistema cumple la **Resolución SET N° 60/2015**. Reglas críticas que nunca deben romperse:

- **IVA inclusivo:** Los precios ya incluyen IVA. Las fórmulas son: `iva_10 = total / 11`, `iva_5 = total / 21`. Ver `app/core/iva_calculator.py`.
- **RUC módulo 11:** Todo RUC debe validarse con el algoritmo del SET. Ver `app/core/ruc_validator.py`. El RUC especial `80069563-1` es "Consumidor Final" y siempre es válido.
- **Numeración correlativa:** Formato `001-001-0000001` (establecimiento-punto-número). La asignación de número solo ocurre al emitir (no al crear borrador). Ver `app/core/numeracion.py`.
- **DOCUMENTO AUTOIMPRESO:** Texto obligatorio en el PDF.
- **Timbrado:** Cada factura emitida requiere número de timbrado vigente de la empresa.
- **Moneda:** Guaraníes paraguayos (PYG), enteros sin centavos.

## Ciclo de vida de una factura

```
BORRADOR → EMITIDA → ANULADA
```

Solo las facturas en `BORRADOR` pueden emitirse. `emitir_factura()` en `factura_service.py` asigna número, calcula totales, genera PDF y opcionalmente dispara SIFEN. Las anulaciones deben incluir un motivo (campo `observacion`).

## SIFEN (Factura Electrónica)

Configurado via `SIFEN_ENABLED=true` en `.env`. El microservicio Node.js vive en `sifen-service/` (librerías oficiales DNIT). La integración Python está en `app/sifen/`. Los estados SIFEN son: `PENDIENTE → ENVIADO → APROBADO | RECHAZADO`. El CDC tiene 44 caracteres y se imprime en el PDF cuando existe.

## Convenciones de código

- Todas las cantidades monetarias se almacenan como `Numeric(15, 2)` en BD pero se muestran como enteros en Guaraníes (sin centavos en la práctica).
- Los enums de SQLAlchemy usan `str, enum.Enum` para serialización JSON directa.
- Los paneles GUI cargan datos en hilo separado y actualizan la UI con `self.after(0, callback)`.
- El dict `C` en `main_window.py` define toda la paleta de colores de la interfaz.
- `data/` está en `.gitignore` — contiene la BD, PDFs generados y certificados SIFEN.
