"""Generador de PDF autoimpreso — formato SET Paraguay."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas


def generar_factura_pdf(factura, empresa) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # ── ENCABEZADO ─────────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, h - 20 * mm, empresa.razon_social if empresa else "EMPRESA")
    c.setFont("Helvetica", 9)
    if empresa:
        c.drawString(20 * mm, h - 26 * mm, f"RUC: {empresa.ruc}  |  {empresa.direccion or ''}")

    # Caja tipo de documento
    c.setFont("Helvetica-Bold", 11)
    c.rect(120 * mm, h - 35 * mm, 75 * mm, 20 * mm)
    c.drawString(122 * mm, h - 22 * mm, factura.tipo_documento.replace("_", " "))
    c.setFont("Helvetica", 9)
    if empresa:
        c.drawString(122 * mm, h - 27 * mm, f"Timbrado: {empresa.timbrado}")
        c.drawString(122 * mm, h - 31 * mm, f"Vigencia: {empresa.timbrado_fecha_inicio} al {empresa.timbrado_fecha_fin}")

    # Número de factura
    c.setFont("Helvetica-Bold", 12)
    numero = factura.numero_completo or "BORRADOR"
    c.drawString(122 * mm, h - 37 * mm, f"N°: {numero}")

    # ── DATOS DEL CLIENTE ──────────────────────────────────────────────────
    y = h - 50 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "DATOS DEL CLIENTE")
    c.line(20 * mm, y - 1 * mm, 190 * mm, y - 1 * mm)
    c.setFont("Helvetica", 9)
    y -= 6 * mm
    cliente = factura.cliente
    c.drawString(20 * mm, y, f"Nombre/Razón Social: {cliente.razon_social if cliente else ''}")
    c.drawString(120 * mm, y, f"RUC/CI: {cliente.ruc_ci if cliente else ''}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Dirección: {cliente.direccion or '' if cliente else ''}")
    c.drawString(120 * mm, y, f"Fecha: {factura.fecha_emision}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Condición de Venta: {factura.condicion_venta}")

    # ── TABLA DE DETALLES ──────────────────────────────────────────────────
    y -= 10 * mm
    encabezados = ["Cant.", "Descripción", "P. Unitario", "Exenta", "5%", "10%"]
    filas = [encabezados]
    for d in factura.detalles:
        exenta = str(int(d.total_linea)) if str(d.tasa_iva.value) == "0" else ""
        cinco = str(int(d.total_linea)) if str(d.tasa_iva.value) == "5" else ""
        diez = str(int(d.total_linea)) if str(d.tasa_iva.value) == "10" else ""
        filas.append([
            str(int(d.cantidad)),
            d.descripcion[:40],
            f"{int(d.precio_unitario):,}",
            exenta, cinco, diez
        ])

    tabla = Table(filas, colWidths=[15 * mm, 80 * mm, 30 * mm, 25 * mm, 20 * mm, 20 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    tabla.wrapOn(c, w, h)
    tabla.drawOn(c, 20 * mm, y - len(filas) * 5 * mm)
    y -= (len(filas) + 1) * 5 * mm

    # ── TOTALES ────────────────────────────────────────────────────────────
    y -= 5 * mm
    c.line(20 * mm, y, 190 * mm, y)
    c.setFont("Helvetica-Bold", 9)
    col_izq = 110 * mm
    col_der = 170 * mm

    def linea_total(label, monto):
        nonlocal y
        y -= 5 * mm
        c.drawString(col_izq, y, label)
        c.drawRightString(col_der, y, f"Gs. {int(monto):,}")

    linea_total("Subtotal Exenta:", factura.subtotal_exenta)
    linea_total("Subtotal Gravada 5%:", factura.subtotal_gravada_5)
    linea_total("IVA 5%:", factura.iva_5)
    linea_total("Subtotal Gravada 10%:", factura.subtotal_gravada_10)
    linea_total("IVA 10%:", factura.iva_10)
    y -= 2 * mm
    c.line(col_izq, y, col_der, y)
    c.setFont("Helvetica-Bold", 11)
    linea_total("TOTAL:", factura.total)

    # ── OBSERVACION ────────────────────────────────────────────────────────
    if factura.observacion:
        y -= 10 * mm
        c.setFont("Helvetica", 8)
        c.drawString(20 * mm, y, f"Obs: {factura.observacion}")

    # ── PIE ────────────────────────────────────────────────────────────────
    c.setFont("Helvetica", 7)
    c.drawString(20 * mm, 15 * mm, "Documento generado por Sistema de Facturación — Paraguay")
    if factura.estado.value == "ANULADA":
        c.setFont("Helvetica-Bold", 36)
        c.setFillColorRGB(1, 0, 0, alpha=0.3)
        c.drawCentredString(w / 2, h / 2, "ANULADA")
        c.setFillColorRGB(0, 0, 0)

    c.save()
    return buffer.getvalue()
