"""Tests para validadores de Paraguay: RUC, cédula, email, teléfono."""
import pytest
from app.core.validators import (
    validar_ruc,
    validar_cedula,
    validar_email,
    validar_telefono,
    formatear_ruc,
    formatear_cedula,
)


# ── RUC ──────────────────────────────────────────────────────────────────────

class TestValidarRuc:
    def test_ruc_valido_con_guion(self):
        assert validar_ruc("80069563-1") is True

    def test_ruc_valido_sin_guion(self):
        assert validar_ruc("800695631") is True

    def test_ruc_con_puntos(self):
        assert validar_ruc("80.069.563-1") is True

    def test_ruc_muy_corto(self):
        assert validar_ruc("123") is False

    def test_ruc_dv_incorrecto(self):
        assert validar_ruc("80069563-2") is False

    def test_ruc_solo_letras(self):
        assert validar_ruc("ABCDEFGH") is False

    def test_ruc_vacio(self):
        assert validar_ruc("") is False


class TestFormatearRuc:
    def test_formatea_digitos(self):
        assert formatear_ruc("800695631") == "80069563-1"

    def test_formatea_con_puntos(self):
        assert formatear_ruc("80.069.563.1") == "80069563-1"

    def test_muy_corto_sin_cambio(self):
        assert formatear_ruc("123") == "123"


# ── Cédula ───────────────────────────────────────────────────────────────────

class TestValidarCedula:
    def test_cedula_valida_5_digitos(self):
        assert validar_cedula("12345") is True

    def test_cedula_valida_8_digitos(self):
        assert validar_cedula("12345678") is True

    def test_cedula_con_puntos(self):
        assert validar_cedula("1.234.567") is True

    def test_cedula_muy_corta(self):
        assert validar_cedula("123") is False

    def test_cedula_muy_larga(self):
        assert validar_cedula("123456789") is False


class TestFormatearCedula:
    def test_quita_puntos(self):
        assert formatear_cedula("1.234.567") == "1234567"

    def test_solo_digitos(self):
        assert formatear_cedula("1234567") == "1234567"


# ── Email ────────────────────────────────────────────────────────────────────

class TestValidarEmail:
    def test_email_valido(self):
        assert validar_email("test@example.com") is True

    def test_email_con_subdominio(self):
        assert validar_email("user@sub.domain.com") is True

    def test_email_sin_arroba(self):
        assert validar_email("userexample.com") is False

    def test_email_sin_dominio(self):
        assert validar_email("user@") is False

    def test_email_sin_tld(self):
        assert validar_email("user@domain") is False


# ── Teléfono ─────────────────────────────────────────────────────────────────

class TestValidarTelefono:
    def test_telefono_9_digitos(self):
        assert validar_telefono("098112345") is True  # 9 dígitos

    def test_telefono_10_digitos(self):
        assert validar_telefono("0981123456") is True  # 10 dígitos

    def test_telefono_con_prefijo_largo(self):
        assert validar_telefono("+595981123456") is False  # 12 dígitos > 10

    def test_telefono_muy_corto(self):
        assert validar_telefono("12345") is False
