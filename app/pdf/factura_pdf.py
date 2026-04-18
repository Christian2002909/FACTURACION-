"""
Generador de PDF autoimpreso — Resolución SET N° 60/2015 — Paraguay.

CAMPOS OBLIGATORIOS según normativa:
  - Nombre/Razón Social del emisor
  - RUC del emisor con dígito verificador
  - Dirección del emisor
  - Actividad económica del emisor
  - Número de timbrado y vigencia (formato DD/MM/YYYY)
  - "DOCUMENTO AUTOIMPRESO" (texto obligatorio SET)
  - Tipo de documento (FACTURA, NOTA DE CRÉDITO, etc.)
  - Número de factura (establecimiento-punto-número)
  - Fecha de emisión (formato DD/MM/YYYY)
  - Nombre/RUC del receptor con tipo de documento
  - Condición de venta y medio de pago
  - Detalle de ítems: cantidad, descripción, precio unitario, descuento, IVA
  - Subtotales por tasa IVA (exenta, 5%, 10%), montos IVA, total
  - CDC SIFEN (si es documento electrónico)
  - Firma del receptor (si es crédito)

FÓRMULAS IVA PARAGUAY (precio incluye impuesto):
  - IVA 10%: monto_iva = total_linea / 11
  - IVA  5%: monto_iva = total_linea / 21
  - Exento:  monto_iva = 0
"""
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4, A5, A6, B5, B6, letter, legal
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
import os


PAPER_SIZES = {
    "carta":     letter,
    "oficio":    (215.9 * mm, 355.6 * mm),
    "ejecutivo": (184.2 * mm, 266.7 * mm),
    "a4":        A4,
    "a5":        A5,
    "a6":        A6,
    "folio":     (215.9 * mm, 330.2 * mm),
    "b5":        B5,
    "b6":        B6,
}

COLOR_SET_AZUL = colors.HexColor("#003366")
COLOR_SET_GRIS = colors.HexColor("#666666")
COLOR_FILA_PAR = colors.HexColor("#f5f8ff")
COLOR_GRILLA   = colors.HexColor("#cccccc")


def _fmt_gs(monto) -> str:
    """Formatea número como Guaraníes: Gs. 1.234.567"""
    try:
        return f"Gs. {int(monto):,}".replace(",", ".")
    except Exception:
        return "Gs. 0"


def _fmt_num(monto) -> str:
    """Formatea número sin prefijo: 1.234.567"""
    try:
        return f"{int(monto):,}".replace(",", ".")
    except Exception:
        return "0"


def _fmt_fecha(d) -> str:
    """Convierte date/string a formato DD/MM/YYYY requerido por SET."""
    if d is None:
        return ""
    if isinstance(d, date):
        return d.strftime("%d/%m/%Y")
    try:
        partes = str(d).split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    except Exception:
        pass
    return str(d)


def _tipo_documento_display(tipo_doc) -> str:
    """Convierte enum TipoDocumento a texto legible con tildes correctas."""
    mapping = {
        "FACTURA":      "FACTURA",
        "NOTA_CREDITO": "NOTA DE CRÉDITO",
        "NOTA_DEBITO":  "NOTA DE DÉBITO",
        "AUTOFACTURA":  "AUTOFACTURA",
    }
    raw = str(getattr(tipo_doc, 'value', tipo_doc))
    return mapping.get(raw, raw.replace("_", " "))


def _tipo_receptor_display(tipo_contribuyente) -> str:
    """Convierte tipo contribuyente a etiqueta para el PDF."""
    mapping = {
        "RUC":        "RUC",
        "CI":         "C.I.",
        "PASAPORTE":  "Pasaporte",
        "EXTRANJERO": "Doc. Extranj.",
    }
    raw = str(getattr(tipo_contribuyente, 'value', tipo_contribuyente))
    return mapping.get(raw, raw)


def generar_factura_pdf(factura, empresa, paper_size="a4") -> bytes:
    """
    Genera PDF de factura en formato autoimpreso.
    Compatible con Resolución SET N° 60/2015.
    Soporta múltiples tamaños de papel con layout dinámico.

    Args:
        factura: instancia de Factura con relaciones cargadas (cliente, detalles, pagos)
        empresa: instancia de Empresa con timbrado vigente
        paper_size: clave de PAPER_SIZES (default "a4")

    Returns:
        bytes del PDF generado
    """
    pagesize = PAPER_SIZES.get(paper_size.lower(), A4) if paper_size else A4
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=pagesize)
    w, h = pagesize

    margin = 15 * mm
    right  = w - margin
    usable = w - 2 * margin

    is_small  = w < 160 * mm
    fs_title  = 11 if is_small else 13
    fs_normal = 7  if is_small else 9
    fs_small  = 6  if is_small else 8
    fs_tiny   = 5  if is_small else 7
    fs_table  = 6  if is_small else 8

    # ── ZONA A: ENCABEZADO EMISOR ──────────────────────────────────────────
    logo_x     = margin
    header_top = h - 15 * mm

    if empresa and empresa.logo_path and os.path.exists(empresa.logo_path):
        try:
            c.drawImage(empresa.logo_path, logo_x, header_top - 22 * mm,
                        width=35 * mm, height=22 * mm,
                        preserveAspectRatio=True, mask="auto")
            logo_x = margin + 38 * mm
        except Exception:
            pass

    ey = header_top
    c.setFont("Helvetica-Bold", fs_title)
    c.setFillColor(COLOR_SET_AZUL)
    c.drawString(logo_x, ey - 5 * mm, empresa.razon_social if empresa else "EMPRESA")

    c.setFont("Helvetica", fs_normal)
    c.setFillColor(colors.black)
    ey -= 10 * mm

    if empresa:
        ruc_line = f"RUC: {empresa.ruc}"
        if empresa.nombre_fantasia:
            ruc_line += f"  |  {empresa.nombre_fantasia}"
        c.drawString(logo_x, ey, ruc_line)
        ey -= 5 * mm

        dir_parts = [empresa.direccion or ""]
        if empresa.ciudad:
            dir_parts.append(empresa.ciudad)
        c.drawString(logo_x, ey, f"Dir.: {', '.join(p for p in dir_parts if p)}")
        ey -= 5 * mm

        contacto = []
        if empresa.telefono:
            contacto.append(f"Tel: {empresa.telefono}")
        if empresa.email:
            contacto.append(f"Email: {empresa.email}")
        if contacto:
            c.drawString(logo_x, ey, "  |  ".join(contacto))
            ey -= 5 * mm

        c.setFont("Helvetica", fs_small)
        c.drawString(logo_x, ey, f"Act. Econ.: {empresa.actividad_economica or ''}")

    # ── RECUADRO TIPO DOCUMENTO (derecha) ──────────────────────────────────
    box_w      = min(75 * mm, usable * 0.42)
    box_h      = 38 * mm
    box_x      = right - box_w
    box_top    = header_top - 3 * mm
    box_center = box_x + box_w / 2
    box_text_x = box_x + 2 * mm

    c.setStrokeColor(COLOR_SET_AZUL)
    c.setLineWidth(1.5)
    c.rect(box_x, box_top - box_h, box_w, box_h)
    c.setLineWidth(0.5)

    c.setFont("Helvetica-Bold", fs_normal + 2)
    c.setFillColor(COLOR_SET_AZUL)
    c.drawCentredString(box_center, box_top - 8 * mm,
                        _tipo_documento_display(factura.tipo_documento))

    c.setFont("Helvetica-Bold", fs_tiny + 1)
    c.setFillColor(COLOR_SET_GRIS)
    c.drawCentredString(box_center, box_top - 13 * mm, "DOCUMENTO AUTOIMPRESO")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", fs_small)

    if empresa:
        c.drawString(box_text_x, box_top - 18 * mm, f"Timbrado N°: {empresa.timbrado}")
        c.drawString(box_text_x, box_top - 23 * mm,
                     f"Vigencia: {_fmt_fecha(empresa.timbrado_fecha_inicio)} al "
                     f"{_fmt_fecha(empresa.timbrado_fecha_fin)}")

    c.setFont("Helvetica-Bold", fs_normal + 2)
    c.setFillColor(COLOR_SET_AZUL)
    c.drawString(box_text_x, box_top - 29 * mm,
                 f"N°: {factura.numero_completo or 'BORRADOR'}")
    c.setFillColor(colors.black)

    c.setFont("Helvetica", fs_small)
    c.drawString(box_text_x, box_top - 34 * mm,
                 f"Fecha: {_fmt_fecha(factura.fecha_emision)}")

    # ── ZONA B: DATOS DEL RECEPTOR ─────────────────────────────────────────
    header_bottom = box_top - box_h - 3 * mm
    c.setStrokeColor(COLOR_SET_AZUL)
    c.setLineWidth(0.5)
    c.line(margin, header_bottom, right, header_bottom)

    receptor_bar_y = header_bottom - 6 * mm
    c.setFillColor(COLOR_SET_AZUL)
    c.rect(margin, receptor_bar_y, usable, 5.5 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", fs_small + 1)
    c.drawString(margin + 2 * mm, receptor_bar_y + 1.2 * mm, "DATOS DEL RECEPTOR")
    c.setFillColor(colors.black)

    y       = receptor_bar_y - 6 * mm
    cliente = factura.cliente
    mid_x   = margin + usable * 0.58

    c.setFont("Helvetica", fs_normal)
    c.drawString(margin, y, f"Nombre/Razón Social: {cliente.razon_social if cliente else ''}")
    if cliente:
        tipo_recv = _tipo_receptor_display(cliente.tipo_contribuyente)
        c.drawString(mid_x, y, f"{tipo_recv}: {cliente.ruc_ci or ''}")
    y -= 5 * mm

    c.drawString(margin, y, f"Dirección: {(cliente.direccion or '') if cliente else ''}")
    c.drawString(mid_x, y, f"Ciudad: {(cliente.ciudad or '') if cliente else ''}")
    y -= 5 * mm

    _cond_raw   = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    _cond_texto = "Al Contado" if _cond_raw == "CONTADO" else "A Crédito"
    c.drawString(margin, y, f"Condición de Venta: {_cond_texto}")
    c.drawString(mid_x, y, f"Moneda: {factura.moneda or 'PYG'}")
    y -= 5 * mm

    if _cond_raw == "CONTADO" and hasattr(factura, 'pagos') and factura.pagos:
        pago0     = factura.pagos[0]
        medio_raw = str(getattr(pago0.medio_pago, 'value', getattr(pago0, 'medio_pago', '')))
        medios    = {
            "EFECTIVO":      "Efectivo",
            "TRANSFERENCIA": "Transferencia Bancaria",
            "CHEQUE":        "Cheque",
            "TARJETA":       "Tarjeta",
            "OTRO":          "Otro",
        }
        c.drawString(margin, y, f"Medio de Pago: {medios.get(medio_raw, medio_raw)}")
        y -= 5 * mm

    c.setStrokeColor(COLOR_SET_AZUL)
    c.line(margin, y + 2 * mm, right, y + 2 * mm)

    # ── ZONA C: TABLA DE ÍTEMS ─────────────────────────────────────────────
    y       -= 5 * mm
    desc_max = 50 if not is_small else 30

    encabezados = ["Cant.", "Descripción", "P. Unit.", "Desc.", "IVA", "Exenta", "5%", "10%"]
    filas = [encabezados]

    for d in factura.detalles:
        tasa  = str(getattr(d.tasa_iva, 'value', d.tasa_iva))
        total = int(d.total_linea) if d.total_linea else 0

        # Usar monto_iva pre-calculado del modelo; recalcular solo como fallback
        iva_item = int(d.monto_iva) if hasattr(d, 'monto_iva') and d.monto_iva else 0
        if iva_item == 0 and total:
            if tasa == "10":
                iva_item = round(total / 11)
            elif tasa == "5":
                iva_item = round(total / 21)

        if tasa == "10":
            exenta, cinco, diez = "", "", _fmt_num(total)
        elif tasa == "5":
            exenta, cinco, diez = "", _fmt_num(total), ""
        else:
            exenta, cinco, diez = _fmt_num(total), "", ""

        desc_monto = int(d.descuento_monto) if hasattr(d, 'descuento_monto') and d.descuento_monto else 0
        desc_str   = _fmt_num(desc_monto) if desc_monto else ""

        try:
            cant_val = float(d.cantidad) if d.cantidad else 1.0
            cant_str = str(int(cant_val)) if cant_val == int(cant_val) else f"{cant_val:.2f}"
        except Exception:
            cant_str = "1"

        filas.append([
            cant_str,
            (d.descripcion or "")[:desc_max],
            _fmt_num(d.precio_unitario) if d.precio_unitario else "0",
            desc_str,
            _fmt_num(iva_item) if iva_item else "",
            exenta, cinco, diez,
        ])

    col_ratios = [0.07, 0.33, 0.13, 0.08, 0.09, 0.10, 0.10, 0.10]
    col_widths = [usable * r for r in col_ratios]

    tabla = Table(filas, colWidths=col_widths)
    tabla.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_SET_AZUL),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), fs_table),
        ("GRID",          (0, 0), (-1, -1), 0.3, COLOR_GRILLA),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (1, 1), (1, -1),  "LEFT"),
        ("ALIGN",         (2, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, COLOR_FILA_PAR]),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
    ]))

    # Usar altura real calculada por ReportLab para posicionamiento correcto
    tabla_w, tabla_h = tabla.wrapOn(c, usable, h)
    tabla.drawOn(c, margin, y - tabla_h)
    y -= tabla_h + 5 * mm

    # ── ZONA D: TOTALES ────────────────────────────────────────────────────
    c.setStrokeColor(COLOR_SET_AZUL)
    c.setLineWidth(0.8)
    c.line(margin, y, right, y)
    y -= 2 * mm

    col_lbl = margin + usable * 0.55
    col_val = right - 2 * mm

    def linea_total(label: str, monto, negrita=False, separador=False):
        nonlocal y
        y -= 5 * mm
        c.setFont("Helvetica-Bold" if negrita else "Helvetica", fs_normal)
        c.setFillColor(COLOR_SET_AZUL if negrita else colors.black)
        c.drawString(col_lbl, y, label)
        c.drawRightString(col_val, y, _fmt_gs(monto))
        c.setFillColor(colors.black)
        if separador:
            c.setStrokeColor(COLOR_SET_AZUL)
            c.line(col_lbl, y - 1.5 * mm, col_val, y - 1.5 * mm)

    sub_exenta = factura.subtotal_exenta or 0
    sub_5      = factura.subtotal_gravada_5 or 0
    sub_10     = factura.subtotal_gravada_10 or 0
    iva_5      = factura.iva_5 or 0
    iva_10     = factura.iva_10 or 0
    total_iva  = factura.total_iva or 0
    total      = factura.total or 0

    if sub_exenta:
        linea_total("Subtotal Exenta:", sub_exenta)
    if sub_5:
        linea_total("Subtotal Gravada 5%:", sub_5)
    if iva_5:
        linea_total("IVA incluido (5%):", iva_5)
    if sub_10:
        linea_total("Subtotal Gravada 10%:", sub_10)
    if iva_10:
        linea_total("IVA incluido (10%):", iva_10)
    linea_total("Total IVA:", total_iva)
    linea_total("TOTAL A PAGAR:", total, negrita=True, separador=True)

    y -= 2 * mm
    c.setFont("Helvetica", fs_tiny)
    c.setFillColor(COLOR_SET_GRIS)
    c.drawString(col_lbl, y, "(IVA incluido en el precio — Res. SET N° 60/2015)")
    c.setFillColor(colors.black)

    # ── ZONA E: CUOTAS (si es crédito) ────────────────────────────────────
    if _cond_raw == "CREDITO" and hasattr(factura, 'pagos') and factura.pagos:
        y -= 8 * mm
        c.setFont("Helvetica-Bold", fs_small)
        c.setFillColor(COLOR_SET_AZUL)
        c.drawString(margin, y, "CUOTAS:")
        c.setFillColor(colors.black)
        for i, pago in enumerate(factura.pagos, 1):
            y -= 4.5 * mm
            c.setFont("Helvetica", fs_small)
            # Modelo Pago usa fecha_pago (fecha_vencimiento no existe en el modelo)
            fecha_pago = _fmt_fecha(pago.fecha_pago) if hasattr(pago, 'fecha_pago') else "S/D"
            medio_raw  = str(getattr(pago.medio_pago, 'value', getattr(pago, 'medio_pago', '')))
            c.drawString(margin + 2 * mm, y,
                         f"Cuota {i}: {_fmt_gs(pago.monto)}  |  Fecha: {fecha_pago}  |  Medio: {medio_raw}")

    # ── ZONA F: CDC SIFEN ─────────────────────────────────────────────────
    if factura.sifen_cdc:
        y -= 6 * mm
        c.setFont("Helvetica-Bold", fs_tiny)
        c.setFillColor(COLOR_SET_GRIS)
        c.drawString(margin, y, "CDC SIFEN:")
        c.setFont("Helvetica", fs_tiny)
        c.drawString(margin + 18 * mm, y, factura.sifen_cdc)
        c.setFillColor(colors.black)

        sifen_estado = str(getattr(factura.sifen_estado, 'value', factura.sifen_estado or ''))
        if sifen_estado:
            y -= 4 * mm
            c.setFont("Helvetica", fs_tiny)
            c.drawString(margin, y, f"Estado SIFEN: {sifen_estado}")

    # ── ZONA G: OBSERVACIONES ─────────────────────────────────────────────
    if factura.observacion:
        y -= 6 * mm
        c.setFont("Helvetica", fs_small)
        obs = factura.observacion
        if len(obs) > 150:
            obs = obs[:147] + "..."
        c.drawString(margin, y, f"Obs.: {obs}")

    # ── ZONA H: FIRMAS ────────────────────────────────────────────────────
    y -= 15 * mm
    firma_w = usable * 0.32
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.line(margin, y, margin + firma_w, y)
    c.setFont("Helvetica", fs_tiny)
    c.drawString(margin, y - 4 * mm, "Firma y Aclaración del Receptor")

    firma2_x = margin + usable * 0.52
    c.line(firma2_x, y, right, y)
    c.drawString(firma2_x, y - 4 * mm, "Aclaración")

    # ── ZONA I: PIE DE PÁGINA ─────────────────────────────────────────────
    pie_y = 12 * mm
    c.setLineWidth(0.5)
    c.setStrokeColor(COLOR_SET_AZUL)
    c.line(margin, pie_y + 4 * mm, right, pie_y + 4 * mm)
    c.setFont("Helvetica", fs_tiny)
    c.setFillColor(COLOR_SET_GRIS)
    timbrado_info = f"Timbrado N° {empresa.timbrado}" if empresa else ""
    c.drawString(margin, pie_y,
                 f"Documento Autoimpreso — Res. SET N° 60/2015 — {timbrado_info}")
    c.drawRightString(right, pie_y, "FacturaPY — Paraguay")
    c.setFillColor(colors.black)

    # ── MARCA DE AGUA ANULADA ─────────────────────────────────────────────
    estado_val = str(getattr(factura.estado, 'value', factura.estado))
    if estado_val == "ANULADA":
        c.saveState()
        wm_size = 48 if is_small else 70
        c.setFont("Helvetica-Bold", wm_size)
        c.setFillColorRGB(1, 0, 0, alpha=0.15)
        # Rotar alrededor del centro de la página
        c.translate(w / 2, h / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, "ANULADA")
        c.restoreState()

    c.save()
    return buffer.getvalue()
