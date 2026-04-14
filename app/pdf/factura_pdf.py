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
from reportlab.lib.pagesizes import A4, A5, A6, B5, B6, letter, legal
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
import os


PAPER_SIZES = {
    "carta": letter,                         # 215.9 x 279.4 mm
    "oficio": (215.9 * mm, 355.6 * mm),     # 215.9 x 355.6 mm (Legal Oficio)
    "ejecutivo": (184.2 * mm, 266.7 * mm),  # 184.2 x 266.7 mm
    "a4": A4,                                # 210 x 297 mm
    "a5": A5,                                # 148 x 210 mm
    "a6": A6,                                # 105 x 148 mm
    "folio": (215.9 * mm, 330.2 * mm),      # 215.9 x 330.2 mm
    "b5": B5,                                # 176 x 250 mm
    "b6": B6,                                # 125 x 176 mm
}


def _fmt_gs(monto) -> str:
    """Formatea número como Guaraníes: Gs. 1.234.567"""
    try:
        return f"Gs. {int(monto):,}".replace(",", ".")
    except Exception:
        return "Gs. 0"


def generar_factura_pdf(factura, empresa, paper_size="a4") -> bytes:
    """
    Genera PDF de factura en formato autoimpreso.
    Compatible con Resolución SET N° 60/2015.
    Soporta múltiples tamaños de papel con layout dinámico.
    """
    pagesize = PAPER_SIZES.get(paper_size.lower(), A4) if paper_size else A4
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesize)
    w, h = pagesize

    margin = 10 * mm
    right = w - margin
    usable = w - 2 * margin  # ancho útil

    # Determine if this is a small page (reduce fonts)
    is_small = w < 160 * mm  # A5, A6, B6, etc.
    fs_title = 11 if is_small else 13
    fs_normal = 8 if is_small else 9
    fs_small = 7 if is_small else 8
    fs_tiny = 6 if is_small else 7
    fs_table = 7 if is_small else 8

    # ── LOGO DE EMPRESA ────────────────────────────────────────────────────
    logo_x = margin
    if empresa and empresa.logo_path and os.path.exists(empresa.logo_path):
        try:
            c.drawImage(empresa.logo_path, logo_x, h - 38 * mm,
                        width=35 * mm, height=22 * mm, preserveAspectRatio=True, mask="auto")
            logo_x = margin + 38 * mm  # texto comienza después del logo
        except Exception:
            pass  # si falla el logo, continúa sin él

    # ── ENCABEZADO EMISOR ──────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", fs_title)
    c.drawString(logo_x, h - 22 * mm, empresa.razon_social if empresa else "EMPRESA")

    c.setFont("Helvetica", fs_normal)
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
            c.setFont("Helvetica", fs_small)
            c.drawString(logo_x, h - 39 * mm, f"Act. Econ.: {empresa.actividad_economica}")

    # ── RECUADRO TIPO DOCUMENTO (derecha) ──────────────────────────────────
    box_w = min(77 * mm, usable * 0.42)
    box_h = 30 * mm
    box_x = right - box_w
    box_center = box_x + box_w / 2

    c.setStrokeColor(colors.HexColor("#003366"))
    c.setLineWidth(1.5)
    c.rect(box_x, h - 42 * mm, box_w, box_h)
    c.setLineWidth(0.5)

    c.setFont("Helvetica-Bold", fs_normal + 1)
    c.setFillColor(colors.HexColor("#003366"))
    tipo_texto = factura.tipo_documento.replace("_", " ") if factura.tipo_documento else "FACTURA"
    c.drawCentredString(box_center, h - 20 * mm, tipo_texto)

    c.setFont("Helvetica-Bold", fs_tiny)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(box_center, h - 24 * mm, "DOCUMENTO AUTOIMPRESO")  # OBLIGATORIO SET

    c.setFillColor(colors.black)
    c.setFont("Helvetica", fs_small)
    if empresa:
        c.drawString(box_x + 2 * mm, h - 28 * mm, f"Timbrado N°: {empresa.timbrado}")
        c.drawString(box_x + 2 * mm, h - 32 * mm, f"Vigencia: {empresa.timbrado_fecha_inicio} al {empresa.timbrado_fecha_fin}")

    c.setFont("Helvetica-Bold", fs_normal + 1)
    numero = factura.numero_completo or "BORRADOR"
    c.drawString(box_x + 2 * mm, h - 37 * mm, f"N°: {numero}")

    # ── DATOS DEL CLIENTE ──────────────────────────────────────────────────
    y = h - 50 * mm
    c.setFillColor(colors.HexColor("#003366"))
    c.rect(margin, y - 1 * mm, usable, 5 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", fs_small)
    c.drawString(margin + 2 * mm, y + 0.5 * mm, "DATOS DEL RECEPTOR")
    c.setFillColor(colors.black)

    c.setFont("Helvetica", fs_normal)
    y -= 6 * mm
    cliente = factura.cliente
    mid_x = margin + usable * 0.57  # punto medio para columnas
    c.drawString(margin, y, f"Nombre/Razón Social: {cliente.razon_social if cliente else ''}")
    c.drawString(mid_x, y, f"RUC/CI: {cliente.ruc_ci if cliente else ''}")
    y -= 5 * mm
    c.drawString(margin, y, f"Dirección: {cliente.direccion or '' if cliente else ''}")
    c.drawString(mid_x, y, f"Fecha: {factura.fecha_emision}")
    y -= 5 * mm
    _cond_raw = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    _cond_texto = "Al Contado" if _cond_raw == "CONTADO" else "A Crédito"
    c.drawString(margin, y, f"Condición de Venta: {_cond_texto}")
    c.drawString(mid_x, y, f"Moneda: {factura.moneda or 'PYG'}")

    # ── TABLA DE DETALLES ──────────────────────────────────────────────────
    y -= 10 * mm
    desc_max = 55 if not is_small else 35
    encabezados = ["Cant.", "Descripción", "P. Unitario", "IVA", "Exenta", "5%", "10%"]
    filas = [encabezados]

    for d in factura.detalles:
        tasa = str(getattr(d.tasa_iva, 'value', d.tasa_iva))
        total = int(d.total_linea) if d.total_linea else 0
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
            (d.descripcion or "")[:desc_max],
            f"{int(d.precio_unitario):,}".replace(",", ".") if d.precio_unitario else "0",
            f"{iva_item:,}".replace(",", "."),
            exenta, cinco, diez
        ])

    # Proportional column widths to fill available width
    # Ratios: Cant(8%) Desc(36%) P.Unit(14%) IVA(12%) Exenta(10%) 5%(10%) 10%(10%)
    col_ratios = [0.08, 0.36, 0.14, 0.12, 0.10, 0.10, 0.10]
    col_widths = [usable * r for r in col_ratios]

    tabla = Table(filas, colWidths=col_widths)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), fs_table),
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
    tabla.drawOn(c, margin, y - filas_alto)
    y -= filas_alto + 8 * mm

    # ── TOTALES ────────────────────────────────────────────────────────────
    c.setStrokeColor(colors.HexColor("#003366"))
    c.line(margin, y, right, y)
    y -= 2 * mm

    col_lbl = margin + usable * 0.55
    col_val = right - 2 * mm

    def linea_total(label: str, monto, negrita=False):
        nonlocal y
        y -= 5 * mm
        c.setFont("Helvetica-Bold" if negrita else "Helvetica", fs_normal)
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
        c.setFont("Helvetica-Bold", fs_small)
        c.drawString(margin, y, "CUOTAS:")
        for i, pago in enumerate(factura.pagos, 1):
            y -= 4 * mm
            c.setFont("Helvetica", fs_small)
            fecha_vto = pago.fecha_vencimiento if hasattr(pago, 'fecha_vencimiento') else 'S/D'
            c.drawString(margin + 2 * mm, y, f"Cuota {i}: {_fmt_gs(pago.monto)} — Vence: {fecha_vto}")

    # ── OBSERVACIÓN ────────────────────────────────────────────────────────
    if factura.observacion:
        y -= 8 * mm
        c.setFont("Helvetica", fs_small)
        c.drawString(margin, y, f"Obs.: {factura.observacion[:120]}")

    # ── FIRMA DEL RECEPTOR ─────────────────────────────────────────────────
    y -= 15 * mm
    firma_w = usable * 0.32
    c.setStrokeColor(colors.black)
    c.line(margin, y, margin + firma_w, y)
    c.setFont("Helvetica", fs_tiny)
    c.drawString(margin, y - 4 * mm, "Firma y Aclaración del Receptor")

    firma2_x = margin + usable * 0.52
    c.line(firma2_x, y, right, y)
    c.drawString(firma2_x, y - 4 * mm, "Aclaración")

    # ── PIE DE PÁGINA ──────────────────────────────────────────────────────
    c.setFont("Helvetica", fs_tiny)
    c.setFillColor(colors.HexColor("#666666"))
    timbrado_info = f"Timbrado N° {empresa.timbrado}" if empresa else ""
    c.drawString(margin, 12 * mm, f"Documento Autoimpreso habilitado por SET — {timbrado_info}")
    c.drawRightString(right, 12 * mm, "Sistema de Facturación — Paraguay")
    c.line(margin, 14 * mm, right, 14 * mm)

    # ── MARCA DE AGUA ANULADA ─────────────────────────────────────────────
    estado_val = str(getattr(factura.estado, 'value', factura.estado))
    if estado_val == "ANULADA":
        c.saveState()
        wm_size = 50 if is_small else 72
        c.setFont("Helvetica-Bold", wm_size)
        c.setFillColorRGB(1, 0, 0, alpha=0.18)
        c.rotate(45)
        c.drawCentredString(w * 0.7, h * 0.05, "ANULADA")
        c.restoreState()

    c.save()
    return buffer.getvalue()
