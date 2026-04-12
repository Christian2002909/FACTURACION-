# 🗺️ PLAN COMPLETO — Sistema FACTURACION- (Paraguay)
# Repo: Christian2002909/FACTURACION-
# Fecha: 2026-04-12
# Stack: Python/FastAPI + SQLAlchemy + ReportLab + Tkinter GUI
# SIFEN: Microservicio Node.js con librerías oficiales DNIT

---

## 📁 ESTRUCTURA ACTUAL DEL REPO

```
FACTURACION-/
├── app/
│   ├── __init__.py
│   ├── cache.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── core/
│   ├── gui/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── caja.py
│   │   ├── cheque.py
│   │   ├── cliente.py        ← OK
│   │   ├── compra.py
│   │   ├── cuota.py
│   │   ├── detalle_factura.py ← VERIFICAR campos
│   │   ├── devolucion.py
│   │   ├── empresa.py        ← OK, tiene timbrado y numero_actual
│   │   ├── factura.py        ← OK, tiene sifen_cdc y sifen_estado
│   │   ├── gasto.py
│   │   ├── pago.py
│   │   ├── producto.py
│   │   └── proveedor.py
│   ├── pdf/
│   │   └── factura_pdf.py    ← CORREGIR (Fase 1)
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   │   └── auth_service.py   ← solo auth, falta factura_service.py
│   └── sifen/
│       ├── __init__.py
│       ├── events.py         ← solo stub con NotImplementedError
│       └── interfaces.py     ← vacío
├── data/
├── migrations/
├── tests/
├── preview_gui.py
├── run.py
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## ORDEN DE EJECUCIÓN

```
Fase 1.3 → Verificar/corregir modelo DetalleFactura
Fase 1.2 → Crear factura_service.py
Fase 1.1 → Corregir factura_pdf.py (autoimpresa SET)
Fase 2   → Completar router facturas + endpoint PDF
Fase 3   → Microservicio Node.js SIFEN (librerías oficiales DNIT)
Fase 4   → Actualizar config.py, .env.example, requirements.txt
Fase 5   → Seguridad básica
```

---

## ══════════════════════════════════════════════
## FASE 1 — FACTURA AUTOIMPRESA (URGENTE)
## Objetivo: Cumplir Resolución SET N° 60/2015
## ══════════════════════════════════════════════

### Fase 1.3 — Verificar `app/models/detalle_factura.py`

Asegurarse que el modelo tenga EXACTAMENTE estos campos:
```python
class TasaIVA(str, enum.Enum):
    EXENTA = "0"
    CINCO = "5"
    DIEZ = "10"

class DetalleFactura(Base):
    __tablename__ = "detalle_factura"
    id: Mapped[int]
    factura_id: Mapped[int]             # FK → factura.id
    descripcion: Mapped[str]            # max 120 chars
    cantidad: Mapped[Decimal]           # Numeric(10,2)
    precio_unitario: Mapped[Decimal]    # Numeric(15,2)
    tasa_iva: Mapped[TasaIVA]           # Enum: "0", "5", "10"
    total_linea: Mapped[Decimal]        # Numeric(15,2) = cantidad * precio_unitario
    # relación:
    factura: Mapped["Factura"]
```

Si falta algún campo o la columna `tasa_iva` es diferente, crear migración:
```bash
alembic revision --autogenerate -m "agregar_tasa_iva_detalle"
alembic upgrade head
```

---

### Fase 1.2 — Crear `app/services/factura_service.py` (NUEVO ARCHIVO)

```python
"""
Servicio centralizado de emisión, cálculo y anulación de facturas.
"""
import os
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.models.factura import Factura, EstadoFactura, EstadoSIFEN
from app.models.empresa import Empresa
from app.models.detalle_factura import DetalleFactura, TasaIVA
from app.pdf.factura_pdf import generar_factura_pdf
from app.config import settings


def calcular_totales(factura: Factura) -> Factura:
    """
    Recorre factura.detalles y calcula todos los subtotales e IVA.
    FÓRMULAS PARAGUAY:
      - IVA incluido en precio: IVA_10 = precio_con_iva / 11
      - IVA incluido en precio: IVA_5  = precio_con_iva / 21
    """
    subtotal_exenta = Decimal("0")
    subtotal_gravada_5 = Decimal("0")
    subtotal_gravada_10 = Decimal("0")

    for d in factura.detalles:
        total = Decimal(str(d.cantidad)) * Decimal(str(d.precio_unitario))
        d.total_linea = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        if str(d.tasa_iva.value) == "0":
            subtotal_exenta += d.total_linea
        elif str(d.tasa_iva.value) == "5":
            subtotal_gravada_5 += d.total_linea
        elif str(d.tasa_iva.value) == "10":
            subtotal_gravada_10 += d.total_linea

    iva_5 = (subtotal_gravada_5 / 21).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    iva_10 = (subtotal_gravada_10 / 11).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    factura.subtotal_exenta = subtotal_exenta
    factura.subtotal_gravada_5 = subtotal_gravada_5
    factura.subtotal_gravada_10 = subtotal_gravada_10
    factura.iva_5 = iva_5
    factura.iva_10 = iva_10
    factura.total_iva = iva_5 + iva_10
    factura.total = subtotal_exenta + subtotal_gravada_5 + subtotal_gravada_10
    return factura


def emitir_factura(db: Session, factura_id: int) -> Factura:
    """
    Cambia estado BORRADOR → EMITIDA, asigna número correlativo,
    genera PDF y opcionalmente dispara SIFEN.
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise ValueError(f"Factura {factura_id} no encontrada")
    if factura.estado != EstadoFactura.BORRADOR:
        raise ValueError(f"Solo se pueden emitir facturas en estado BORRADOR. Estado actual: {factura.estado}")

    empresa = db.query(Empresa).first()
    if not empresa:
        raise ValueError("No hay empresa configurada en el sistema")

    # Calcular totales
    factura = calcular_totales(factura)

    # Asignar número correlativo ATÓMICO
    numero_str = str(empresa.numero_actual).zfill(7)
    factura.timbrado = empresa.timbrado
    factura.establecimiento = empresa.establecimiento
    factura.punto_expedicion = empresa.punto_expedicion
    factura.numero = numero_str
    factura.numero_completo = f"{empresa.establecimiento}-{empresa.punto_expedicion}-{numero_str}"
    empresa.numero_actual += 1

    # Cambiar estado
    factura.estado = EstadoFactura.EMITIDA

    # Generar PDF en disco
    os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
    pdf_bytes = generar_factura_pdf(factura, empresa)
    pdf_path = os.path.join(settings.PDF_OUTPUT_DIR, f"{factura.numero_completo}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    factura.pdf_path = pdf_path

    db.commit()
    db.refresh(factura)

    # Disparar SIFEN si está habilitado
    if settings.SIFEN_ENABLED:
        from app.sifen.events import on_factura_emitida
        on_factura_emitida(factura.id)

    return factura


def anular_factura(db: Session, factura_id: int, motivo: str) -> Factura:
    """
    Anula una factura emitida. No se puede anular una electrónica aprobada
    directamente (requiere nota de crédito).
    """
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise ValueError("Factura no encontrada")
    if factura.estado != EstadoFactura.EMITIDA:
        raise ValueError("Solo se pueden anular facturas emitidas")
    if factura.sifen_estado == EstadoSIFEN.APROBADO:
        raise ValueError(
            "No se puede anular una factura electrónica aprobada por SIFEN. "
            "Debe emitir una Nota de Crédito Electrónica."
        )

    factura.estado = EstadoFactura.ANULADA
    factura.observacion = motivo

    # Regenerar PDF con marca de agua ANULADA
    empresa = db.query(Empresa).first()
    pdf_bytes = generar_factura_pdf(factura, empresa)
    if factura.pdf_path:
        with open(factura.pdf_path, "wb") as f:
            f.write(pdf_bytes)

    db.commit()
    db.refresh(factura)
    return factura
```

---

### Fase 1.1 — Corregir `app/pdf/factura_pdf.py` (REEMPLAZAR COMPLETO)

```python
"""
Generador de PDF autoimpreso — Resolución SET N° 60/2015 — Paraguay.
CAMPOS OBLIGATORIOS según normativa:
  - Nombre/Razón Social del emisor
  - RUC del emisor
  - Dirección del emisor
  - Número de timbrado y vigencia
  - "DOCUMENTO AUTOIMPRESO" (texto obligatorio)
  - Tipo de documento
  - Número de factura (establecimiento-punto-número)
  - Fecha de emisión
  - Nombre/RUC del receptor
  - Condición de venta
  - Detalle de ítems con cantidad, descripción, precio unitario
  - Subtotales por tasa IVA, montos IVA, total
  - Firma del receptor (si es crédito)
"""
from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
import os


def _fmt_gs(monto) -> str:
    """Formatea número como Guaraníes: Gs. 1.234.567"""
    try:
        return f"Gs. {int(monto):,}".replace(",", ".")
    except Exception:
        return "Gs. 0"


def generar_factura_pdf(factura, empresa) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # ── LOGO DE EMPRESA ────────────────────────────────────────────────────
    logo_x = 20 * mm
    if empresa and empresa.logo_path and os.path.exists(empresa.logo_path):
        try:
            c.drawImage(empresa.logo_path, logo_x, h - 38 * mm,
                        width=35 * mm, height=22 * mm, preserveAspectRatio=True, mask="auto")
            logo_x = 58 * mm  # texto comienza después del logo
        except Exception:
            pass  # si falla el logo, continúa sin él

    # ── ENCABEZADO EMISOR ──────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 13)
    c.drawString(logo_x, h - 22 * mm, empresa.razon_social if empresa else "EMPRESA")

    c.setFont("Helvetica", 9)
    if empresa:
        linea_ruc = f"RUC: {empresa.ruc}"
        if empresa.nombre_fantasia:
            linea_ruc += f"  |  {empresa.nombre_fantasia}"
        c.drawString(logo_x, h - 27 * mm, linea_ruc)
        c.drawString(logo_x, h - 31 * mm, f"Dir: {empresa.direccion or ''}{', ' + empresa.ciudad if empresa.ciudad else ''}")
        partes_contacto = []
        if empresa.telefono:
            partes_contacto.append(f"Tel: {empresa.telefono}")
        if empresa.email:
            partes_contacto.append(f"Email: {empresa.email}")
        if partes_contacto:
            c.drawString(logo_x, h - 35 * mm, "  |  ".join(partes_contacto))
        if empresa.actividad_economica:
            c.setFont("Helvetica", 8)
            c.drawString(logo_x, h - 39 * mm, f"Act. Econ.: {empresa.actividad_economica}")

    # ── RECUADRO TIPO DOCUMENTO (derecha) ──────────────────────────────────
    c.setStrokeColor(colors.HexColor("#003366"))
    c.setLineWidth(1.5)
    c.rect(118 * mm, h - 42 * mm, 77 * mm, 30 * mm)
    c.setLineWidth(0.5)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#003366"))
    tipo_texto = factura.tipo_documento.replace("_", " ") if factura.tipo_documento else "FACTURA"
    c.drawCentredString(156 * mm, h - 20 * mm, tipo_texto)

    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(156 * mm, h - 24 * mm, "DOCUMENTO AUTOIMPRESO")  # OBLIGATORIO SET

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    if empresa:
        c.drawString(120 * mm, h - 28 * mm, f"Timbrado N°: {empresa.timbrado}")
        c.drawString(120 * mm, h - 32 * mm, f"Vigencia: {empresa.timbrado_fecha_inicio} al {empresa.timbrado_fecha_fin}")

    c.setFont("Helvetica-Bold", 10)
    numero = factura.numero_completo or "BORRADOR"
    c.drawString(120 * mm, h - 37 * mm, f"N°: {numero}")

    # ── DATOS DEL CLIENTE ──────────────────────────────────────────────────
    y = h - 50 * mm
    c.setFillColor(colors.HexColor("#003366"))
    c.rect(20 * mm, y - 1 * mm, 175 * mm, 5 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(22 * mm, y + 0.5 * mm, "DATOS DEL RECEPTOR")
    c.setFillColor(colors.black)

    c.setFont("Helvetica", 9)
    y -= 7 * mm
    cliente = factura.cliente
    c.drawString(20 * mm, y, f"Nombre/Razón Social: {cliente.razon_social if cliente else ''}")
    c.drawString(130 * mm, y, f"RUC/CI: {cliente.ruc_ci if cliente else ''}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Dirección: {(cliente.direccion or '') if cliente else ''}")
    c.drawString(130 * mm, y, f"Fecha: {factura.fecha_emision}")
    y -= 5 * mm

    cond_texto = "Al Contado" if str(getattr(factura.condicion_venta, 'value', factura.condicion_venta)) == "CONTADO" else "A Crédito"
    c.drawString(20 * mm, y, f"Condición de Venta: {cond_texto}")
    c.drawString(130 * mm, y, f"Moneda: {factura.moneda or 'PYG'}")

    # ── TABLA DE ÍTEMS ─────────────────────────────────────────────────────
    y -= 10 * mm
    encabezados = ["Cant.", "Descripción", "P. Unitario", "IVA", "Exenta", "5%", "10%"]
    filas = [encabezados]

    for d in factura.detalles:
        tasa = str(getattr(d.tasa_iva, 'value', d.tasa_iva))
        total = int(d.total_linea) if d.total_linea else 0
        # Calcular IVA del ítem
        if tasa == "10":
            iva_item = round(total / 11)
            exenta, cinco, diez = "", "", f"{total:,}".replace(",", ".")
        elif tasa == "5":
            iva_item = round(total / 21)
            exenta, cinco, diez = "", f"{total:,}".replace(",", "."), ""
        else:
            iva_item = 0
            exenta, cinco, diez = f"{total:,}".replace(",", "."), "", ""

        filas.append([
            str(int(d.cantidad)) if d.cantidad else "1",
            (d.descripcion or "")[:45],
            f"{int(d.precio_unitario):,}".replace(",", ".") if d.precio_unitario else "0",
            f"{iva_item:,}".replace(",", "."),
            exenta, cinco, diez
        ])

    col_widths = [15*mm, 68*mm, 27*mm, 22*mm, 20*mm, 18*mm, 18*mm]
    tabla = Table(filas, colWidths=col_widths)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    filas_alto = len(filas) * 5 * mm
    tabla.wrapOn(c, w, h)
    tabla.drawOn(c, 20 * mm, y - filas_alto)
    y -= filas_alto + 8 * mm

    # ── TOTALES ────────────────────────────────────────────────────────────
    c.setStrokeColor(colors.HexColor("#003366"))
    c.line(20 * mm, y, 195 * mm, y)
    y -= 2 * mm

    col_lbl = 115 * mm
    col_val = 190 * mm

    def linea_total(label: str, monto, negrita=False):
        nonlocal y
        y -= 5 * mm
        c.setFont("Helvetica-Bold" if negrita else "Helvetica", 9)
        c.drawString(col_lbl, y, label)
        c.drawRightString(col_val, y, _fmt_gs(monto))

    linea_total("Subtotal Exenta:", factura.subtotal_exenta)
    linea_total("Subtotal Gravada 5%:", factura.subtotal_gravada_5)
    linea_total("IVA (5%):", factura.iva_5)
    linea_total("Subtotal Gravada 10%:", factura.subtotal_gravada_10)
    linea_total("IVA (10%):", factura.iva_10)
    linea_total("Total IVA:", factura.total_iva)
    y -= 1 * mm
    c.line(col_lbl, y, col_val, y)
    linea_total("TOTAL:", factura.total, negrita=True)

    # ── CUOTAS (si es crédito) ─────────────────────────────────────────────
    cond_val = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    if cond_val == "CREDITO" and hasattr(factura, 'pagos') and factura.pagos:
        y -= 8 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20 * mm, y, "CUOTAS:")
        for i, pago in enumerate(factura.pagos, 1):
            y -= 4 * mm
            c.setFont("Helvetica", 8)
            c.drawString(22 * mm, y, f"Cuota {i}: {_fmt_gs(pago.monto)} — Vence: {pago.fecha_vencimiento if hasattr(pago, 'fecha_vencimiento') else 'S/D'}")

    # ── OBSERVACIÓN ────────────────────────────────────────────────────────
    if factura.observacion:
        y -= 8 * mm
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, y, f"Obs.: {factura.observacion[:120]}")

    # ── FIRMA DEL RECEPTOR ─────────────────────────────────────────────────
    y -= 15 * mm
    c.setStrokeColor(colors.black)
    c.line(20 * mm, y, 80 * mm, y)
    c.setFont("Helvetica", 7)
    c.drawString(20 * mm, y - 4 * mm, "Firma y Aclaración del Receptor")

    c.line(110 * mm, y, 190 * mm, y)
    c.drawString(110 * mm, y - 4 * mm, "Aclaración")

    # ── PIE DE PÁGINA ──────────────────────────────────────────────────────
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#666666"))
    timbrado_info = f"Timbrado N° {empresa.timbrado}" if empresa else ""
    c.drawString(20 * mm, 12 * mm, f"Documento Autoimpreso habilitado por SET — {timbrado_info}")
    c.drawRightString(190 * mm, 12 * mm, f"Sistema de Facturación — Paraguay")
    c.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)

    # ── MARCA DE AGUA ANULADA ─────────────────────────────────────────────
    estado_val = str(getattr(factura.estado, 'value', factura.estado))
    if estado_val == "ANULADA":
        c.saveState()
        c.setFont("Helvetica-Bold", 72)
        c.setFillColorRGB(1, 0, 0, alpha=0.18)
        c.rotate(45)
        c.drawCentredString(200 * mm, 20 * mm, "ANULADA")
        c.restoreState()

    c.save()
    return buffer.getvalue()
```

---

## ══════════════════════════════════════════════
## FASE 2 — ROUTER Y ENDPOINT PDF
## ══════════════════════════════════════════════

### Fase 2.1 — Verificar/crear `app/routers/facturas.py`

Asegurarse que existan EXACTAMENTE estos endpoints:

```python
# app/routers/facturas.py
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.factura import Factura, EstadoFactura
from app.models.empresa import Empresa
from app.pdf.factura_pdf import generar_factura_pdf
from app.services.factura_service import emitir_factura, anular_factura

router = APIRouter(prefix="/facturas", tags=["Facturas"])

# GET /facturas/ — listar con filtros
@router.get("/")
def listar_facturas(
    estado: str = None,
    cliente_id: int = None,
    fecha_desde: str = None,
    fecha_hasta: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Factura)
    if estado:
        query = query.filter(Factura.estado == estado)
    if cliente_id:
        query = query.filter(Factura.cliente_id == cliente_id)
    if fecha_desde:
        query = query.filter(Factura.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Factura.fecha_emision <= fecha_hasta)
    return query.order_by(Factura.created_at.desc()).offset(skip).limit(limit).all()

# GET /facturas/{id} — detalle con ítems
@router.get("/{factura_id}")
def obtener_factura(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura

# POST /facturas/{id}/emitir — emitir y generar PDF
@router.post("/{factura_id}/emitir")
def emitir(factura_id: int, db: Session = Depends(get_db)):
    try:
        return emitir_factura(db, factura_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# GET /facturas/{id}/pdf — descargar PDF
@router.get("/{factura_id}/pdf")
def descargar_pdf(factura_id: int, db: Session = Depends(get_db)):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if factura.estado == EstadoFactura.BORRADOR:
        raise HTTPException(status_code=400, detail="No se puede descargar PDF de un borrador. Primero emitir.")
    if factura.pdf_path and os.path.exists(factura.pdf_path):
        return FileResponse(factura.pdf_path, media_type="application/pdf",
                            filename=f"factura_{factura.numero_completo}.pdf")
    # Generar en memoria si no hay archivo
    empresa = db.query(Empresa).first()
    pdf_bytes = generar_factura_pdf(factura, empresa)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=factura_{factura.numero_completo or factura_id}.pdf"})

# POST /facturas/{id}/anular
@router.post("/{factura_id}/anular")
def anular(factura_id: int, motivo: str, db: Session = Depends(get_db)):
    try:
        return anular_factura(db, factura_id, motivo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

Registrar el router en `app/main.py` si no está:
```python
from app.routers.facturas import router as facturas_router
app.include_router(facturas_router)
```

---

## ══════════════════════════════════════════════
## FASE 3 — MÓDULO SIFEN (FACTURA ELECTRÓNICA)
## Librerías oficiales DNIT e-Kuatia (Node.js)
## Solo activo si SIFEN_ENABLED=true en .env
## ══════════════════════════════════════════════

### CONTEXTO IMPORTANTE

El DNIT (ex-SET) Paraguay publica librerías oficiales de código abierto para e-Kuatia:
- Todas están en **Node.js** (no Python)
- Fuente oficial: https://www.dnit.gov.py/web/e-kuatia/librerias
- Librerías a usar:
  1. `facturacionelectronicapy-xmlgen` — genera XML del Documento Electrónico (DE) según Manual Técnico SIFEN v150
  2. `facturacionelectronicapy-xmlsign` — firma el XML con certificado PKCS#12 del contribuyente
  3. `facturacionelectronicapy-setapi` — envía el DE al webservice SOAP de SIFEN (test y producción)

**Estrategia:** Crear un microservicio Node.js en `/sifen-service/` que expone endpoints HTTP internos (localhost:3001). El código Python llama a este microservicio con httpx.

---

### Fase 3.1 — Crear `/sifen-service/` (microservicio Node.js)

#### `/sifen-service/package.json`
```json
{
  "name": "sifen-service",
  "version": "1.0.0",
  "description": "Microservicio SIFEN para facturacion electronica Paraguay",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "facturacionelectronicapy-xmlgen": "latest",
    "facturacionelectronicapy-xmlsign": "latest",
    "facturacionelectronicapy-setapi": "latest",
    "express": "^4.18.0"
  }
}
```

#### `/sifen-service/index.js`
```javascript
const express = require('express');
const { generateXML } = require('facturacionelectronicapy-xmlgen');
const { signXML } = require('facturacionelectronicapy-xmlsign');
const { sendDE, cancelDE, inutilizeDE, consultDE } = require('facturacionelectronicapy-setapi');

const app = express();
app.use(express.json({ limit: '10mb' }));

// Solo aceptar conexiones locales
app.listen(3001, '127.0.0.1', () => {
  console.log('SIFEN service escuchando en localhost:3001');
});

// POST /generar-xml → recibe {params, data} → retorna {xml}
app.post('/generar-xml', async (req, res) => {
  try {
    const { params, data } = req.body;
    const xml = await generateXML(params, data);
    res.json({ xml });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /firmar-xml → recibe {xml, certPath, certPassword} → retorna {xmlFirmado}
app.post('/firmar-xml', async (req, res) => {
  try {
    const { xml, certPath, certPassword } = req.body;
    const xmlFirmado = await signXML(xml, certPath, certPassword);
    res.json({ xmlFirmado });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /enviar-sifen → recibe {xml, ambiente} → retorna {cdc, estado, protocolo, mensaje}
app.post('/enviar-sifen', async (req, res) => {
  try {
    const { xml, ambiente } = req.body;
    const resultado = await sendDE(xml, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /cancelar → recibe {cdc, motivo, params, ambiente} → retorna resultado
app.post('/cancelar', async (req, res) => {
  try {
    const { cdc, motivo, params, ambiente } = req.body;
    const resultado = await cancelDE(cdc, motivo, params, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// POST /consultar → recibe {cdc, ambiente} → retorna estado actual en SIFEN
app.post('/consultar', async (req, res) => {
  try {
    const { cdc, ambiente } = req.body;
    const resultado = await consultDE(cdc, ambiente === 'prod' ? 'prod' : 'test');
    res.json(resultado);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

---

### Fase 3.2 — Crear `app/sifen/client.py` (cliente Python → Node.js)

```python
"""
Cliente Python para el microservicio SIFEN Node.js.
Convierte los modelos SQLAlchemy a JSON según estructura
del Manual Técnico SIFEN v150 (facturacionelectronicapy-xmlgen).
"""
import httpx
import random
from sqlalchemy.orm import Session
from app.config import settings

SIFEN_SERVICE_URL = "http://127.0.0.1:3001"


def construir_params(empresa) -> dict:
    """
    Construye el objeto 'params' estático del emisor.
    Este objeto describe la empresa emisora para xmlgen.
    """
    return {
        "version": 150,
        "ruc": empresa.ruc.replace("-", ""),        # solo dígitos sin DV
        "dv": empresa.ruc.split("-")[-1] if "-" in empresa.ruc else "0",
        "razonSocial": empresa.razon_social,
        "nombreFantasia": empresa.nombre_fantasia or empresa.razon_social,
        "actividadesEconomicas": [
            {"codigo": "00000", "descripcion": empresa.actividad_economica or "COMERCIO"}
        ],
        "timbradoNumero": empresa.timbrado,
        "timbradoFecha": str(empresa.timbrado_fecha_inicio),
        "tipoContribuyente": 1,   # 1=Persona Física, 2=Persona Jurídica
        "tipoRegimen": 8,         # 8=Régimen general
        "establecimientos": [{
            "codigo": empresa.establecimiento,
            "direccion": empresa.direccion,
            "numeroCasa": "0",
            "departamento": 11,                     # Alto Paraná
            "departamentoDescripcion": "ALTO PARANA",
            "distrito": 145,                        # ajustar según empresa
            "distritoDescripcion": "CIUDAD DEL ESTE",
            "ciudad": 3432,
            "ciudadDescripcion": "CIUDAD DEL ESTE",
            "telefono": empresa.telefono or "0",
            "email": empresa.email or ""
        }]
    }


def construir_data(factura) -> dict:
    """
    Construye el objeto 'data' variable por cada factura.
    Mapea el modelo Factura + DetalleFactura → JSON xmlgen.
    """
    cliente = factura.cliente

    # Determinar tipo de documento
    tipo_doc_map = {
        "FACTURA": 1,
        "NOTA_CREDITO": 5,
        "NOTA_DEBITO": 6,
        "AUTOFACTURA": 4
    }
    tipo_doc = tipo_doc_map.get(
        str(getattr(factura.tipo_documento, 'value', factura.tipo_documento)), 1
    )

    # Condición de venta: 1=Contado, 2=Crédito
    cond_val = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    tipo_condicion = 1 if cond_val == "CONTADO" else 2

    # Ítems
    items = []
    for i, d in enumerate(factura.detalles, 1):
        tasa = int(str(getattr(d.tasa_iva, 'value', d.tasa_iva)))
        items.append({
            "codigo": str(i),
            "descripcion": d.descripcion,
            "observacion": "",
            "unidadMedida": 77,        # 77=Unidad, ver tabla MT SIFEN
            "cantidad": float(d.cantidad),
            "precioUnitario": float(d.precio_unitario),
            "ivaTipo": 1,              # 1=IVA incluido en precio
            "ivaBase": 100,
            "iva": tasa,               # 0, 5 o 10
            "lote": None,
            "vencimiento": None
        })

    return {
        "tipoDocumento": tipo_doc,
        "establecimiento": factura.establecimiento,
        "punto": factura.punto_expedicion,
        "numero": factura.numero,
        "codigoSeguridadAleatorio": str(random.randint(100000000, 999999999)),
        "fecha": str(factura.fecha_emision) + "T00:00:00",
        "tipoEmision": 1,              # 1=Normal, 2=Contingencia
        "tipoTransaccion": 1,          # 1=Venta de mercadería
        "tipoImpuesto": 1,             # 1=IVA
        "moneda": factura.moneda or "PYG",
        "cliente": {
            "contribuyente": True,
            "ruc": (cliente.ruc_ci or "").replace("-", "") if cliente else "0",
            "dv": cliente.ruc_ci.split("-")[-1] if cliente and cliente.ruc_ci and "-" in cliente.ruc_ci else "0",
            "razonSocial": cliente.razon_social if cliente else "SIN NOMBRE",
            "pais": "PRY",
            "tipoContribuyente": 1,
            "documentoTipo": 1,
            "telefono": cliente.telefono if cliente and hasattr(cliente, 'telefono') else "0",
            "email": cliente.email if cliente and hasattr(cliente, 'email') else ""
        },
        "condicion": {
            "tipo": tipo_condicion,
            "entregas": [{"tipo": 1, "monto": float(factura.total)}] if tipo_condicion == 1 else []
        },
        "items": items
    }


def generar_y_enviar_de(factura, empresa) -> dict:
    """
    Flujo completo: genera XML → firma → envía a SIFEN.
    Retorna dict con {cdc, estado, protocolo, mensaje}.
    """
    ambiente = getattr(settings, 'SIFEN_AMBIENTE', 'test')
    params = construir_params(empresa)
    data = construir_data(factura)

    try:
        # 1. Generar XML
        r = httpx.post(f"{SIFEN_SERVICE_URL}/generar-xml",
                       json={"params": params, "data": data}, timeout=30)
        r.raise_for_status()
        xml = r.json()["xml"]

        # 2. Firmar XML
        r = httpx.post(f"{SIFEN_SERVICE_URL}/firmar-xml",
                       json={
                           "xml": xml,
                           "certPath": settings.SIFEN_CERT_PATH,
                           "certPassword": settings.SIFEN_CERT_PASSWORD
                       }, timeout=30)
        r.raise_for_status()
        xml_firmado = r.json()["xmlFirmado"]

        # 3. Enviar a SIFEN
        r = httpx.post(f"{SIFEN_SERVICE_URL}/enviar-sifen",
                       json={"xml": xml_firmado, "ambiente": ambiente}, timeout=60)
        r.raise_for_status()
        return r.json()

    except httpx.HTTPError as e:
        raise RuntimeError(f"Error comunicando con microservicio SIFEN: {e}")


def cancelar_de(cdc: str, motivo: str, empresa) -> dict:
    """Cancela un DE aprobado en SIFEN."""
    ambiente = getattr(settings, 'SIFEN_AMBIENTE', 'test')
    params = construir_params(empresa)
    r = httpx.post(f"{SIFEN_SERVICE_URL}/cancelar",
                   json={"cdc": cdc, "motivo": motivo,
                         "params": params, "ambiente": ambiente}, timeout=30)
    r.raise_for_status()
    return r.json()


def consultar_estado_de(cdc: str) -> dict:
    """Consulta el estado actual de un DE en SIFEN por CDC."""
    ambiente = getattr(settings, 'SIFEN_AMBIENTE', 'test')
    r = httpx.post(f"{SIFEN_SERVICE_URL}/consultar",
                   json={"cdc": cdc, "ambiente": ambiente}, timeout=30)
    r.raise_for_status()
    return r.json()
```

---

### Fase 3.3 — Reemplazar `app/sifen/events.py` (completo)

```python
"""
Eventos disparados después de operaciones de facturación.
Solo activos si SIFEN_ENABLED=true en .env
"""
from app.config import settings


def on_factura_emitida(factura_id: int) -> None:
    """Disparado por factura_service.emitir_factura() luego de guardar en BD."""
    if not settings.SIFEN_ENABLED:
        return

    # Importación tardía para evitar circular imports
    from app.database import SessionLocal
    from app.models.factura import Factura, EstadoSIFEN
    from app.models.empresa import Empresa
    from app.sifen.client import generar_y_enviar_de

    db = SessionLocal()
    try:
        factura = db.query(Factura).filter(Factura.id == factura_id).first()
        empresa = db.query(Empresa).first()

        if not factura or not empresa:
            return

        factura.sifen_estado = EstadoSIFEN.PENDIENTE
        db.commit()

        resultado = generar_y_enviar_de(factura, empresa)
        cdc = resultado.get("cdc") or resultado.get("id")
        estado_sifen = resultado.get("estado", "")

        factura.sifen_cdc = cdc
        if "Aprobado" in estado_sifen:
            factura.sifen_estado = EstadoSIFEN.APROBADO
        elif "Rechazado" in estado_sifen:
            factura.sifen_estado = EstadoSIFEN.RECHAZADO
            factura.observacion = resultado.get("mensaje", "Rechazado por SIFEN")
        else:
            factura.sifen_estado = EstadoSIFEN.ENVIADO

        db.commit()

    except Exception as e:
        # No romper el flujo principal si SIFEN falla
        if factura:
            factura.sifen_estado = EstadoSIFEN.RECHAZADO
            factura.observacion = f"Error SIFEN: {str(e)[:200]}"
            db.commit()
    finally:
        db.close()
```

---

### Fase 3.4 — Agregar endpoint para cancelar DE en el router

```python
# Agregar en app/routers/facturas.py

@router.post("/{factura_id}/cancelar-de")
def cancelar_de_sifen(factura_id: int, motivo: str, db: Session = Depends(get_db)):
    """Cancela un DE aprobado en SIFEN (solo ambiente test o producción)."""
    from app.sifen.client import cancelar_de
    from app.models.factura import EstadoSIFEN

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(404, "Factura no encontrada")
    if factura.sifen_estado != EstadoSIFEN.APROBADO:
        raise HTTPException(400, "Solo se puede cancelar un DE con estado APROBADO en SIFEN")
    if not factura.sifen_cdc:
        raise HTTPException(400, "La factura no tiene CDC asignado")

    empresa = db.query(Empresa).first()
    try:
        resultado = cancelar_de(factura.sifen_cdc, motivo, empresa)
        factura.estado = EstadoFactura.ANULADA
        factura.observacion = f"Cancelado en SIFEN: {motivo}"
        db.commit()
        return resultado
    except Exception as e:
        raise HTTPException(500, str(e))
```

---

## ══════════════════════════════════════════════
## FASE 4 — CONFIGURACIÓN Y DEPENDENCIAS
## ══════════════════════════════════════════════

### Fase 4.1 — Actualizar `app/config.py`

Agregar al modelo Settings:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... campos existentes ...

    # PDF
    PDF_OUTPUT_DIR: str = "data/facturas/"

    # SIFEN
    SIFEN_ENABLED: bool = False
    SIFEN_AMBIENTE: str = "test"         # "test" o "prod"
    SIFEN_CERT_PATH: str = "data/certificados/cert.p12"
    SIFEN_CERT_PASSWORD: str = ""
    SIFEN_CONTRIBUYENTE_TIPO: int = 1    # 1=Física, 2=Jurídica

    class Config:
        env_file = ".env"
```

### Fase 4.2 — Actualizar `.env.example`

```env
# Base de datos
DATABASE_URL=sqlite:///./data/facturacion.db

# JWT Auth
SECRET_KEY=cambiar_esto_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# PDF
PDF_OUTPUT_DIR=data/facturas/

# Factura Electrónica SIFEN (desactivado por defecto)
SIFEN_ENABLED=false
SIFEN_AMBIENTE=test
SIFEN_CERT_PATH=data/certificados/cert.p12
SIFEN_CERT_PASSWORD=
SIFEN_CONTRIBUYENTE_TIPO=1

# Documentación oficial DNIT:
# https://www.dnit.gov.py/web/e-kuatia/documentacion
# Guía de pruebas:
# https://www.dnit.gov.py/documents/20123/424160/Guia+de+Pruebas+para+e-kuatia.pdf
```

### Fase 4.3 — Actualizar `requirements.txt`

Agregar:
```
httpx>=0.27.0        # cliente HTTP para llamar al microservicio SIFEN
Pillow>=10.0.0       # para renderizar logo en el PDF
```

### Fase 4.4 — Actualizar `.gitignore`

Agregar estas líneas:
```gitignore
# PDFs generados
data/facturas/

# Certificados digitales (NUNCA commitear)
data/certificados/
*.p12
*.pfx
*.pem
*.key

# Base de datos
*.db
*.sqlite
```

### Fase 4.5 — Crear directorios necesarios en `run.py`

Agregar al inicio de `run.py`:
```python
import os
os.makedirs("data/facturas", exist_ok=True)
os.makedirs("data/certificados", exist_ok=True)
os.makedirs("data/backups", exist_ok=True)
```

---

## ══════════════════════════════════════════════
## FASE 5 — SEGURIDAD BÁSICA
## ══════════════════════════════════════════════

### Fase 5.1 — CORS restrictivo en `app/main.py`

Reemplazar:
```python
# ANTES (inseguro):
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# DESPUÉS:
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Fase 5.2 — Crear `app/core/validators.py`

```python
"""Validadores para datos específicos de Paraguay."""
import re

def validar_ruc(ruc: str) -> bool:
    """
    Valida RUC paraguayo: NNNNNNN-D
    donde D es el dígito verificador módulo 11.
    También acepta RUC sin guión (NNNNNNNND).
    """
    ruc = ruc.strip().upper()
    # Normalizar: quitar todo excepto dígitos
    solo_digitos = re.sub(r'[^0-9]', '', ruc)
    if len(solo_digitos) < 2:
        return False

    numero = solo_digitos[:-1]
    dv_ingresado = int(solo_digitos[-1])

    # Calcular dígito verificador módulo 11
    k = 2
    suma = 0
    for d in reversed(numero):
        suma += int(d) * k
        k = k + 1 if k < 9 else 2

    resto = suma % 11
    dv_calculado = 0 if resto < 2 else 11 - resto

    return dv_calculado == dv_ingresado


def validar_cedula(ci: str) -> bool:
    """Valida cédula paraguaya: solo dígitos, 5-8 caracteres."""
    ci_limpio = re.sub(r'[^0-9]', '', ci)
    return 4 <= len(ci_limpio) <= 8


def formatear_ruc(ruc: str) -> str:
    """Formatea RUC como NNNNNNN-D."""
    solo_digitos = re.sub(r'[^0-9]', '', ruc)
    if len(solo_digitos) >= 2:
        return f"{solo_digitos[:-1]}-{solo_digitos[-1]}"
    return ruc
```

---

## ══════════════════════════════════════════════
## RESUMEN ARCHIVOS A CREAR / MODIFICAR
## ══════════════════════════════════════════════

| Archivo | Acción | Fase |
|---|---|---|
| `app/models/detalle_factura.py` | VERIFICAR/CORREGIR campos | 1.3 |
| `app/services/factura_service.py` | CREAR NUEVO | 1.2 |
| `app/pdf/factura_pdf.py` | REEMPLAZAR COMPLETO | 1.1 |
| `app/routers/facturas.py` | VERIFICAR/COMPLETAR | 2.1 |
| `sifen-service/package.json` | CREAR NUEVO | 3.1 |
| `sifen-service/index.js` | CREAR NUEVO | 3.1 |
| `app/sifen/client.py` | CREAR NUEVO | 3.2 |
| `app/sifen/events.py` | REEMPLAZAR COMPLETO | 3.3 |
| `app/config.py` | ACTUALIZAR | 4.1 |
| `.env.example` | ACTUALIZAR | 4.2 |
| `requirements.txt` | ACTUALIZAR | 4.3 |
| `.gitignore` | ACTUALIZAR | 4.4 |
| `run.py` | ACTUALIZAR | 4.5 |
| `app/main.py` | CORREGIR CORS | 5.1 |
| `app/core/validators.py` | CREAR NUEVO | 5.2 |

---

## ══════════════════════════════════════════════
## RESULTADO ESPERADO
## ══════════════════════════════════════════════

### Al terminar Fase 1 + 2:
✅ PDF autoimpreso cumple Resolución SET N° 60/2015
✅ Logo de empresa en el encabezado del PDF
✅ Leyenda "DOCUMENTO AUTOIMPRESO" presente
✅ Numeración correlativa automática (001-001-0000001)
✅ IVA discriminado por ítem y por tasa en totales
✅ Cuadro de firma del receptor
✅ API endpoint `/facturas/{id}/pdf` funcional
✅ Servicio centralizado de emisión y anulación

### Al terminar Fase 3:
✅ Microservicio Node.js con librerías oficiales DNIT
✅ Generación de XML según MT SIFEN v150
✅ Firma digital con certificado PKCS#12 del SET
✅ Envío al webservice e-Kuatia (test primero, luego prod)
✅ Estado SIFEN actualizado en BD (PENDIENTE/APROBADO/RECHAZADO)
✅ Cancelación de DE aprobados
✅ Sistema unificado: misma factura soporta autoimpresa y electrónica

### URLs de referencia DNIT:
- Documentación: https://www.dnit.gov.py/web/e-kuatia/documentacion
- Librerías: https://www.dnit.gov.py/web/e-kuatia/librerias
- Guía pruebas: https://www.dnit.gov.py/documents/20123/424160/Guia+de+Pruebas+para+e-kuatia.pdf
- Ambiente test: https://sifen-test.set.gov.py/de/ws/sync/recibe.wsdl
- Ambiente prod: https://sifen.set.gov.py/de/ws/sync/recibe.wsdl
