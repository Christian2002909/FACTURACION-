"""
Validadores específicos para Paraguay
RUC, cédula de identidad y otros datos locales
"""
import re


def validar_ruc(ruc: str) -> bool:
    """
    Valida RUC paraguayo: NNNNNNN-D
    donde D es el dígito verificador módulo 11.
    También acepta RUC sin guión (NNNNNNNND).

    Fórmula: Módulo 11 en base 2-9
    - Se multiplica cada dígito (de derecha a izquierda) por 2-9 cíclicamente
    - Se suma todo y se aplica módulo 11
    - Si resto < 2 → DV = 0, si no → DV = 11 - resto

    Args:
        ruc: RUC en formato "NNNNNNN-D" o "NNNNNNNND"

    Returns:
        True si el RUC es válido, False si no
    """
    ruc = ruc.strip().upper()

    # Normalizar: quitar todo excepto dígitos
    solo_digitos = re.sub(r'[^0-9]', '', ruc)

    # Debe tener al menos 8 dígitos
    if len(solo_digitos) < 8:
        return False

    numero = solo_digitos[:-1]  # Todos menos el último
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
    """
    Valida cédula de identidad paraguaya.
    Formato: solo dígitos, entre 5 y 8 caracteres.

    Args:
        ci: Cédula de identidad en formato "NNNNNNN" o similar

    Returns:
        True si es válida, False si no
    """
    ci_limpio = re.sub(r'[^0-9]', '', ci)
    return 4 <= len(ci_limpio) <= 8


def formatear_ruc(ruc: str) -> str:
    """
    Formatea RUC como NNNNNNN-D.

    Args:
        ruc: RUC sin formato o parcialmente formateado

    Returns:
        RUC en formato "NNNNNNN-D"
    """
    solo_digitos = re.sub(r'[^0-9]', '', ruc)
    if len(solo_digitos) >= 8:
        return f"{solo_digitos[:-1]}-{solo_digitos[-1]}"
    return ruc


def formatear_cedula(ci: str) -> str:
    """
    Normaliza cédula de identidad (solo dígitos).

    Args:
        ci: Cédula con o sin formato

    Returns:
        Cédula solo con dígitos
    """
    return re.sub(r'[^0-9]', '', ci)


def validar_email(email: str) -> bool:
    """
    Validación básica de email.

    Args:
        email: Dirección de correo

    Returns:
        True si tiene formato básico válido
    """
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, email))


def validar_telefono(telefono: str) -> bool:
    """
    Validación básica de teléfono Paraguay.
    Formato: 9-10 dígitos, opcionalmente con + al inicio.

    Args:
        telefono: Número telefónico

    Returns:
        True si tiene formato válido
    """
    solo_digitos = re.sub(r'[^0-9]', '', telefono)
    return 9 <= len(solo_digitos) <= 10
