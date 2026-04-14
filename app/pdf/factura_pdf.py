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
    """
    Genera PDF de factura en formato autoimpreso.
    Compatible con Resolución SET N° 60/2015.
    """
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
    y -= 6 * mm
    cliente = factura.cliente
    c.drawString(20 * mm, y, f"Nombre/Razón Social: {cliente.razon_social if cliente else ''}")
    c.drawString(120 * mm, y, f"RUC/CI: {cliente.ruc_ci if cliente else ''}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Dirección: {cliente.direccion or '' if cliente else ''}")
    c.drawString(120 * mm, y, f"Fecha: {factura.fecha_emision}")
    y -= 5 * mm
    # Parsear condición de venta: evitar imprimir el enum raw
    _cond_raw = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    _cond_texto = "Al Contado" if _cond_raw == "CONTADO" else "A Crédito"
    c.drawString(20 * mm, y, f"Condición de Venta: {_cond_texto}")
    c.drawString(120 * mm, y, f"Moneda: {factura.moneda or 'PYG'}")

    # ── TABLA DE DETALLES ──────────────────────────────────────────────────
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
            (d.descripcion or "")[:55],  # tabla ancha permite más caracteres
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
            fecha_vto = pago.fecha_vencimiento if hasattr(pago, 'fecha_vencimiento') else 'S/D'
            c.drawString(22 * mm, y, f"Cuota {i}: {_fmt_gs(pago.monto)} — Vence: {fecha_vto}")

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
