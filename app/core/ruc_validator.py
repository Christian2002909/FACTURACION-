"""
Validador de RUC Paraguay — Algoritmo módulo-11 del SET.
Formato: NNNNNNNNN-D  (1-8 dígitos base + guión + 1 dígito verificador)
"""
from app.core.exceptions import RUCInvalidoError

CONSUMIDOR_FINAL = "80069563-1"


def validar_ruc(ruc: str) -> str:
    """Valida y normaliza un RUC paraguayo. Retorna el RUC limpio o lanza RUCInvalidoError."""
    ruc = ruc.strip().upper()

    if ruc == CONSUMIDOR_FINAL:
        return ruc

    if "-" not in ruc:
        raise RUCInvalidoError(f"RUC inválido '{ruc}': debe contener guión separador (ej: 12345678-9)")

    partes = ruc.split("-")
    if len(partes) != 2:
        raise RUCInvalidoError(f"RUC inválido '{ruc}': formato debe ser NNNNNNNNN-D")

    base, dv = partes

    if not base.isdigit() or not dv.isdigit():
        raise RUCInvalidoError(f"RUC inválido '{ruc}': solo se permiten dígitos")

    if not (1 <= len(base) <= 8):
        raise RUCInvalidoError(f"RUC inválido '{ruc}': la parte base debe tener entre 1 y 8 dígitos")

    if len(dv) != 1:
        raise RUCInvalidoError(f"RUC inválido '{ruc}': el dígito verificador debe ser un solo dígito")

    dv_calculado = _calcular_dv(base)
    if int(dv) != dv_calculado:
        raise RUCInvalidoError(f"RUC inválido '{ruc}': dígito verificador incorrecto (esperado {dv_calculado})")

    return ruc


def _calcular_dv(base: str) -> int:
    """Calcula el dígito verificador módulo-11 del SET Paraguay."""
    numero = int(base)
    suma = 0
    multiplicador = 2

    while numero > 0:
        digito = numero % 10
        suma += digito * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 9 else 2
        numero //= 10

    resto = suma % 11
    if resto <= 1:
        return 0
    return 11 - resto
