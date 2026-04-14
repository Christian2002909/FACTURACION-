"""
Configuración centralizada — FacturaPY — Sistema de Gestión Comercial
Variables de entorno desde .env
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de aplicación desde variables de entorno."""

    # ── AUTENTICACIÓN ──────────────────────────────────────────────────
    APP_USERNAME: str = "admin"
    APP_PASSWORD_HASH: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── BASE DE DATOS ──────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/facturacion.db"

    # ── PDF ────────────────────────────────────────────────────────────
    PDF_OUTPUT_DIR: str = "data/facturas"

    # ── SIFEN (Factura Electrónica) ────────────────────────────────────
    SIFEN_ENABLED: bool = False
    SIFEN_AMBIENTE: str = "test"  # "test" o "prod"
    SIFEN_CERT_PATH: str = "data/certificados/cert.p12"
    SIFEN_CERT_PASSWORD: str = ""
    SIFEN_CONTRIBUYENTE_TIPO: int = 1  # 1=Física, 2=Jurídica

    # ── CONFIGURACIÓN ADMIN ───────────────────────────────────────────
    ADMIN_CONFIG_PASSWORD: str = "admin_config_2026"  # default que debe cambiarse

    model_config = {"env_file": ".env"}


settings = Settings()
