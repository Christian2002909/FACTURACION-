from decimal import Decimal
from app.core.iva_calculator import calcular_iva_linea, calcular_totales


def test_iva_10():
    res = calcular_iva_linea(Decimal("110000"), "10")
    assert res.monto_iva == 10000
    assert res.base_imponible == 100000
    assert res.total_linea == 110000


def test_iva_5():
    res = calcular_iva_linea(Decimal("105000"), "5")
    assert res.monto_iva == 5000
    assert res.base_imponible == 100000


def test_iva_exento():
    res = calcular_iva_linea(Decimal("50000"), "0")
    assert res.monto_iva == 0
    assert res.base_imponible == 50000


def test_totales_mixtos():
    lineas = [
        {"total_linea": Decimal("110000"), "tasa_iva": "10"},
        {"total_linea": Decimal("105000"), "tasa_iva": "5"},
        {"total_linea": Decimal("50000"), "tasa_iva": "0"},
    ]
    t = calcular_totales(lineas)
    assert t.iva_10 == 10000
    assert t.iva_5 == 5000
    assert t.subtotal_exenta == 50000
    assert t.total_iva == 15000
    assert t.total == 265000
