"""
Calculador de IVA Paraguay.
En Paraguay los precios son IVA-INCLUSIVO por convención legal.
  10%: iva = round(total * 10 / 110)
   5%: iva = round(total * 5 / 105)
   0%: iva = 0
Todo en PYG (enteros, sin centavos).
"""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass


@dataclass
class ResultadoIVA:
    total_linea: int
    monto_iva: int
    base_imponible: int
    tasa: str


def calcular_iva_linea(total_linea: Decimal, tasa: str) -> ResultadoIVA:
    total = int(total_linea.to_integral_value(rounding=ROUND_HALF_UP))

    if tasa == "10":
        iva = round(total * 10 / 110)
    elif tasa == "5":
        iva = round(total * 5 / 105)
    else:
        iva = 0

    base = total - iva
    return ResultadoIVA(total_linea=total, monto_iva=iva, base_imponible=base, tasa=tasa)


@dataclass
class TotalesFactura:
    subtotal_exenta: int
    subtotal_gravada_5: int
    subtotal_gravada_10: int
    iva_5: int
    iva_10: int
    total_iva: int
    total: int


def calcular_totales(lineas: list[dict]) -> TotalesFactura:
    """
    lineas: lista de dicts con keys: total_linea (Decimal), tasa_iva (str)
    """
    exenta = gravada_5 = gravada_10 = iva_5 = iva_10 = 0

    for linea in lineas:
        res = calcular_iva_linea(Decimal(str(linea["total_linea"])), linea["tasa_iva"])
        if linea["tasa_iva"] == "0":
            exenta += res.total_linea
        elif linea["tasa_iva"] == "5":
            gravada_5 += res.base_imponible
            iva_5 += res.monto_iva
        elif linea["tasa_iva"] == "10":
            gravada_10 += res.base_imponible
            iva_10 += res.monto_iva

    return TotalesFactura(
        subtotal_exenta=exenta,
        subtotal_gravada_5=gravada_5,
        subtotal_gravada_10=gravada_10,
        iva_5=iva_5,
        iva_10=iva_10,
        total_iva=iva_5 + iva_10,
        total=exenta + gravada_5 + iva_5 + gravada_10 + iva_10,
    )
