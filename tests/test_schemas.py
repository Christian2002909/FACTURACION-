"""Tests para validación de schemas Pydantic — FacturaPY"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.factura import FacturaCreate, DetalleFacturaCreate, FacturaUpdate
from app.schemas.producto import ProductoCreate
from app.schemas.pago import PagoCreate
from app.models.factura import TipoDocumento, CondicionVenta
from app.models.enums import TasaIVA
from app.models.pago import MedioPago


# ── DetalleFacturaCreate ─────────────────────────────────────────────────────

class TestDetalleFacturaCreate:
    def _detalle(self, **overrides):
        base = {
            "descripcion": "Producto test",
            "cantidad": Decimal("1"),
            "precio_unitario": Decimal("100000"),
            "tasa_iva": TasaIVA.DIEZ,
        }
        base.update(overrides)
        return DetalleFacturaCreate(**base)

    def test_detalle_valido(self):
        d = self._detalle()
        assert d.descripcion == "Producto test"
        assert d.cantidad == Decimal("1")

    def test_cantidad_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._detalle(cantidad=Decimal("0"))

    def test_cantidad_negativa_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._detalle(cantidad=Decimal("-1"))

    def test_precio_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._detalle(precio_unitario=Decimal("0"))

    def test_precio_negativo_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._detalle(precio_unitario=Decimal("-500"))

    def test_descuento_mayor_100_falla(self):
        with pytest.raises(ValidationError, match="less_than_equal"):
            self._detalle(descuento_porcentaje=Decimal("150"))

    def test_descuento_negativo_falla(self):
        with pytest.raises(ValidationError, match="greater_than_equal"):
            self._detalle(descuento_porcentaje=Decimal("-10"))

    def test_descuento_100_valido(self):
        d = self._detalle(descuento_porcentaje=Decimal("100"))
        assert d.descuento_porcentaje == Decimal("100")

    def test_descripcion_vacia_falla(self):
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            self._detalle(descripcion="")

    def test_orden_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than_equal"):
            self._detalle(orden=0)


# ── FacturaCreate ────────────────────────────────────────────────────────────

class TestFacturaCreate:
    def _factura(self, **overrides):
        base = {
            "fecha_emision": date.today(),
            "cliente_id": 1,
            "detalles": [
                {
                    "descripcion": "Servicio",
                    "cantidad": Decimal("1"),
                    "precio_unitario": Decimal("100000"),
                    "tasa_iva": TasaIVA.DIEZ,
                }
            ],
        }
        base.update(overrides)
        return FacturaCreate(**base)

    def test_factura_valida(self):
        f = self._factura()
        assert f.cliente_id == 1
        assert len(f.detalles) == 1

    def test_fecha_futura_falla(self):
        with pytest.raises(ValidationError, match="no puede ser futura"):
            self._factura(fecha_emision=date.today() + timedelta(days=1))

    def test_fecha_hoy_valida(self):
        f = self._factura(fecha_emision=date.today())
        assert f.fecha_emision == date.today()

    def test_fecha_pasada_valida(self):
        f = self._factura(fecha_emision=date.today() - timedelta(days=30))
        assert f.fecha_emision < date.today()

    def test_cliente_id_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._factura(cliente_id=0)

    def test_cliente_id_negativo_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            self._factura(cliente_id=-1)

    def test_sin_detalles_falla(self):
        with pytest.raises(ValidationError, match="at least 1"):
            self._factura(detalles=[])

    def test_condicion_venta_default(self):
        f = self._factura()
        assert f.condicion_venta == CondicionVenta.CONTADO

    def test_tipo_documento_default(self):
        f = self._factura()
        assert f.tipo_documento == TipoDocumento.FACTURA

    def test_observacion_larga_falla(self):
        with pytest.raises(ValidationError, match="String should have at most 1000"):
            self._factura(observacion="x" * 1001)


# ── FacturaUpdate ────────────────────────────────────────────────────────────

class TestFacturaUpdate:
    def test_update_fecha_futura_falla(self):
        with pytest.raises(ValidationError, match="no puede ser futura"):
            FacturaUpdate(fecha_emision=date.today() + timedelta(days=5))

    def test_update_parcial_valido(self):
        u = FacturaUpdate(observacion="nota actualizada")
        assert u.observacion == "nota actualizada"
        assert u.fecha_emision is None


# ── ProductoCreate ───────────────────────────────────────────────────────────

class TestProductoCreate:
    def test_producto_valido(self):
        p = ProductoCreate(
            codigo="P001",
            descripcion="Monitor 24 pulgadas",
            precio_unitario=Decimal("550000"),
        )
        assert p.codigo == "P001"

    def test_codigo_vacio_falla(self):
        with pytest.raises(ValidationError, match="at least 1"):
            ProductoCreate(
                codigo="",
                descripcion="Monitor",
                precio_unitario=Decimal("550000"),
            )

    def test_precio_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            ProductoCreate(
                codigo="P001",
                descripcion="Monitor",
                precio_unitario=Decimal("0"),
            )

    def test_precio_negativo_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            ProductoCreate(
                codigo="P001",
                descripcion="Monitor",
                precio_unitario=Decimal("-100"),
            )

    def test_descripcion_vacia_falla(self):
        with pytest.raises(ValidationError, match="at least 1"):
            ProductoCreate(
                codigo="P001",
                descripcion="",
                precio_unitario=Decimal("100"),
            )


# ── PagoCreate ───────────────────────────────────────────────────────────────

class TestPagoCreate:
    def test_pago_valido(self):
        p = PagoCreate(
            factura_id=1,
            fecha_pago=date.today(),
            monto=Decimal("50000"),
        )
        assert p.monto == Decimal("50000")

    def test_monto_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            PagoCreate(
                factura_id=1,
                fecha_pago=date.today(),
                monto=Decimal("0"),
            )

    def test_monto_negativo_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            PagoCreate(
                factura_id=1,
                fecha_pago=date.today(),
                monto=Decimal("-100"),
            )

    def test_fecha_futura_falla(self):
        with pytest.raises(ValidationError, match="no puede ser futura"):
            PagoCreate(
                factura_id=1,
                fecha_pago=date.today() + timedelta(days=1),
                monto=Decimal("50000"),
            )

    def test_factura_id_cero_falla(self):
        with pytest.raises(ValidationError, match="greater_than"):
            PagoCreate(
                factura_id=0,
                fecha_pago=date.today(),
                monto=Decimal("50000"),
            )

    def test_medio_pago_default(self):
        p = PagoCreate(
            factura_id=1,
            fecha_pago=date.today(),
            monto=Decimal("50000"),
        )
        assert p.medio_pago == MedioPago.EFECTIVO
