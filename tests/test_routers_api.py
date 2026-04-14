"""
Tests de integración para endpoints API — FacturaPY
Usa TestClient de FastAPI con BD en memoria.
"""
import pytest
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Auth ─────────────────────────────────────────────────────────────────────

class TestAuthEndpoints:
    def test_login_sin_credenciales(self):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    def test_login_credenciales_invalidas(self):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "bad", "password": "bad"},
        )
        assert resp.status_code == 401

    def test_refresh_token_invalido(self):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token"},
        )
        assert resp.status_code == 401


# ── Clientes ─────────────────────────────────────────────────────────────────

class TestClienteEndpoints:
    def test_listar_sin_auth(self):
        resp = client.get("/api/v1/clientes")
        assert resp.status_code == 401

    def test_crear_cliente(self, auth_headers):
        resp = client.post(
            "/api/v1/clientes",
            json={
                "tipo_contribuyente": "CI",
                "ruc_ci": "1234567",
                "razon_social": "Juan Pérez",
                "direccion": "Calle 1",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["razon_social"] == "Juan Pérez"
        assert data["activo"] is True

    def test_crear_y_obtener_cliente(self, auth_headers):
        # Crear
        create_resp = client.post(
            "/api/v1/clientes",
            json={
                "tipo_contribuyente": "CI",
                "razon_social": "María López",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        cliente_id = create_resp.json()["id"]

        # Obtener
        get_resp = client.get(f"/api/v1/clientes/{cliente_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["razon_social"] == "María López"

    def test_obtener_cliente_inexistente(self, auth_headers):
        resp = client.get("/api/v1/clientes/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_eliminar_cliente_soft_delete(self, auth_headers):
        # Crear
        create_resp = client.post(
            "/api/v1/clientes",
            json={
                "tipo_contribuyente": "CI",
                "razon_social": "Para Borrar",
            },
            headers=auth_headers,
        )
        cliente_id = create_resp.json()["id"]

        # Eliminar (soft)
        del_resp = client.delete(f"/api/v1/clientes/{cliente_id}", headers=auth_headers)
        assert del_resp.status_code == 204

        # Verificar que sigue existiendo pero inactivo
        get_resp = client.get(f"/api/v1/clientes/{cliente_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["activo"] is False


# ── Productos ────────────────────────────────────────────────────────────────

class TestProductoEndpoints:
    def test_listar_sin_auth(self):
        resp = client.get("/api/v1/productos")
        assert resp.status_code == 401

    def test_crear_producto(self, auth_headers):
        resp = client.post(
            "/api/v1/productos",
            json={
                "codigo": "TEST001",
                "descripcion": "Teclado USB",
                "precio_unitario": "55000",
                "tasa_iva": "10",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "TEST001"
        assert data["activo"] is True

    def test_crear_producto_precio_negativo(self, auth_headers):
        resp = client.post(
            "/api/v1/productos",
            json={
                "codigo": "NEG001",
                "descripcion": "Producto inválido",
                "precio_unitario": "-100",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_crear_producto_codigo_vacio(self, auth_headers):
        resp = client.post(
            "/api/v1/productos",
            json={
                "codigo": "",
                "descripcion": "Sin código",
                "precio_unitario": "100",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_buscar_producto_por_codigo(self, auth_headers):
        # Crear
        client.post(
            "/api/v1/productos",
            json={
                "codigo": "BUSCAR001",
                "descripcion": "Para buscar",
                "precio_unitario": "10000",
            },
            headers=auth_headers,
        )

        # Buscar
        resp = client.get(
            "/api/v1/productos/buscar?codigo=BUSCAR001",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["codigo"] == "BUSCAR001"

    def test_buscar_producto_inexistente(self, auth_headers):
        resp = client.get(
            "/api/v1/productos/buscar?codigo=NOEXISTE",
            headers=auth_headers,
        )
        assert resp.status_code == 404


# ── Facturas ─────────────────────────────────────────────────────────────────

class TestFacturaEndpoints:
    def _crear_cliente(self, headers):
        resp = client.post(
            "/api/v1/clientes",
            json={
                "tipo_contribuyente": "CI",
                "razon_social": "Cliente Factura",
            },
            headers=headers,
        )
        return resp.json()["id"]

    def test_crear_factura_valida(self, auth_headers):
        cliente_id = self._crear_cliente(auth_headers)
        resp = client.post(
            "/api/v1/facturas",
            json={
                "fecha_emision": str(date.today()),
                "cliente_id": cliente_id,
                "detalles": [
                    {
                        "descripcion": "Servicio consultoría",
                        "cantidad": "1",
                        "precio_unitario": "110000",
                        "tasa_iva": "10",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["estado"] == "BORRADOR"
        assert data["cliente_id"] == cliente_id

    def test_crear_factura_sin_detalles_falla(self, auth_headers):
        cliente_id = self._crear_cliente(auth_headers)
        resp = client.post(
            "/api/v1/facturas",
            json={
                "fecha_emision": str(date.today()),
                "cliente_id": cliente_id,
                "detalles": [],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_crear_factura_fecha_futura_falla(self, auth_headers):
        from datetime import timedelta
        cliente_id = self._crear_cliente(auth_headers)
        resp = client.post(
            "/api/v1/facturas",
            json={
                "fecha_emision": str(date.today() + timedelta(days=5)),
                "cliente_id": cliente_id,
                "detalles": [
                    {
                        "descripcion": "Servicio",
                        "cantidad": "1",
                        "precio_unitario": "100000",
                        "tasa_iva": "10",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_crear_factura_cantidad_negativa_falla(self, auth_headers):
        cliente_id = self._crear_cliente(auth_headers)
        resp = client.post(
            "/api/v1/facturas",
            json={
                "fecha_emision": str(date.today()),
                "cliente_id": cliente_id,
                "detalles": [
                    {
                        "descripcion": "Servicio",
                        "cantidad": "-1",
                        "precio_unitario": "100000",
                        "tasa_iva": "10",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_obtener_factura_inexistente(self, auth_headers):
        resp = client.get("/api/v1/facturas/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_listar_facturas_vacio(self, auth_headers):
        resp = client.get("/api/v1/facturas", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []


# ── Pagos ────────────────────────────────────────────────────────────────────

class TestPagoEndpoints:
    def test_listar_pagos_sin_auth(self):
        resp = client.get("/api/v1/pagos")
        assert resp.status_code == 401

    def test_crear_pago_monto_negativo(self, auth_headers):
        resp = client.post(
            "/api/v1/pagos",
            json={
                "factura_id": 1,
                "fecha_pago": str(date.today()),
                "monto": "-100",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_crear_pago_fecha_futura(self, auth_headers):
        from datetime import timedelta
        resp = client.post(
            "/api/v1/pagos",
            json={
                "factura_id": 1,
                "fecha_pago": str(date.today() + timedelta(days=3)),
                "monto": "50000",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ── Configuración ────────────────────────────────────────────────────────────

class TestConfigEndpoints:
    def test_health_check(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["app"] == "FacturaPY"

    def test_obtener_empresa_sin_auth(self):
        resp = client.get("/api/v1/config/empresa")
        assert resp.status_code == 401

    def test_verificar_admin_password_incorrecto(self, auth_headers):
        resp = client.post(
            "/api/v1/config/verify-admin",
            json={"password": "wrong"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
