import pytest
from app.core.ruc_validator import validar_ruc
from app.core.exceptions import RUCInvalidoError


def test_ruc_valido():
    assert validar_ruc("80069563-1") == "80069563-1"


def test_consumidor_final():
    assert validar_ruc("80069563-1") == "80069563-1"


def test_ruc_sin_guion():
    with pytest.raises(RUCInvalidoError):
        validar_ruc("800695631")


def test_ruc_dv_incorrecto():
    with pytest.raises(RUCInvalidoError):
        validar_ruc("80069563-2")


def test_ruc_con_letras():
    with pytest.raises(RUCInvalidoError):
        validar_ruc("8006956A-1")


def test_ruc_base_muy_larga():
    with pytest.raises(RUCInvalidoError):
        validar_ruc("123456789-0")
