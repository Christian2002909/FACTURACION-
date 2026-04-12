"""
Cliente Python para el microservicio SIFEN Node.js.
Convierte modelos SQLAlchemy a JSON según Manual Técnico SIFEN v150.
"""
import httpx
import random
from decimal import Decimal
from app.config import settings

SIFEN_SERVICE_URL = "http://127.0.0.1:3001"


def construir_params(empresa) -> dict:
    """Construye objeto 'params' estático del emisor para xmlgen."""
    ruc_sin_dv = empresa.ruc.split("-")[0] if "-" in empresa.ruc else empresa.ruc
    dv = empresa.ruc.split("-")[-1] if "-" in empresa.ruc else "0"

    return {
        "version": 150,
        "ruc": ruc_sin_dv,
        "dv": dv,
        "razonSocial": empresa.razon_social,
        "nombreFantasia": empresa.nombre_fantasia or empresa.razon_social,
        "actividadesEconomicas": [
            {"codigo": "00000", "descripcion": empresa.actividad_economica or "COMERCIO"}
        ],
        "timbradoNumero": empresa.timbrado,
        "timbradoFecha": str(empresa.timbrado_fecha_inicio),
        "tipoContribuyente": 1,
        "tipoRegimen": 8,
        "establecimientos": [{
            "codigo": empresa.establecimiento,
            "direccion": empresa.direccion,
            "numeroCasa": "0",
            "departamento": 11,
            "departamentoDescripcion": "ALTO PARANA",
            "distrito": 145,
            "distritoDescripcion": "CIUDAD DEL ESTE",
            "ciudad": 3432,
            "ciudadDescripcion": "CIUDAD DEL ESTE",
            "telefono": empresa.telefono or "0",
            "email": empresa.email or ""
        }]
    }


def construir_data(factura) -> dict:
    """Construye objeto 'data' variable por cada factura."""
    cliente = factura.cliente

    tipo_doc_map = {
        "FACTURA": 1,
        "NOTA_CREDITO": 5,
        "NOTA_DEBITO": 6,
        "AUTOFACTURA": 4
    }
    tipo_doc = tipo_doc_map.get(
        str(getattr(factura.tipo_documento, 'value', factura.tipo_documento)), 1
    )

    cond_val = str(getattr(factura.condicion_venta, 'value', factura.condicion_venta))
    tipo_condicion = 1 if cond_val == "CONTADO" else 2

    items = []
    for i, d in enumerate(factura.detalles, 1):
        tasa = int(str(getattr(d.tasa_iva, 'value', d.tasa_iva)))
        items.append({
            "codigo": str(i),
            "descripcion": d.descripcion,
            "observacion": "",
            "unidadMedida": 77,
            "cantidad": float(d.cantidad),
            "precioUnitario": float(d.precio_unitario),
            "ivaTipo": 1,
            "ivaBase": 100,
            "iva": tasa,
            "lote": None,
            "vencimiento": None
        })

    cliente_ruc = (cliente.ruc_ci or "").replace("-", "") if cliente else "0"
    cliente_dv = cliente.ruc_ci.split("-")[-1] if cliente and cliente.ruc_ci and "-" in cliente.ruc_ci else "0"

    return {
        "tipoDocumento": tipo_doc,
        "establecimiento": factura.establecimiento,
        "punto": factura.punto_expedicion,
        "numero": factura.numero,
        "codigoSeguridadAleatorio": str(random.randint(100000000, 999999999)),
        "fecha": str(factura.fecha_emision) + "T00:00:00",
        "tipoEmision": 1,
        "tipoTransaccion": 1,
        "tipoImpuesto": 1,
        "moneda": factura.moneda or "PYG",
        "cliente": {
            "contribuyente": True,
            "ruc": cliente_ruc,
            "dv": cliente_dv,
            "razonSocial": cliente.razon_social if cliente else "SIN NOMBRE",
            "pais": "PRY",
            "tipoContribuyente": 1,
            "documentoTipo": 1,
            "telefono": (cliente.telefono if cliente and hasattr(cliente, 'telefono') else "0") or "0",
            "email": (cliente.email if cliente and hasattr(cliente, 'email') else "") or ""
        },
        "condicion": {
            "tipo": tipo_condicion,
            "entregas": [{"tipo": 1, "monto": float(factura.total)}] if tipo_condicion == 1 else []
        },
        "items": items
    }


def generar_y_enviar_de(factura, empresa) -> dict:
    """Flujo completo: genera XML → firma → envía a SIFEN."""
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
    """Consulta estado actual de un DE en SIFEN por CDC."""
    ambiente = getattr(settings, 'SIFEN_AMBIENTE', 'test')
    r = httpx.post(f"{SIFEN_SERVICE_URL}/consultar",
                   json={"cdc": cdc, "ambiente": ambiente}, timeout=30)
    r.raise_for_status()
    return r.json()
