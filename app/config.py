from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_USERNAME: str = "admin"
    APP_PASSWORD_HASH: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    DATABASE_URL: str = "sqlite:///./data/facturacion.db"
    SIFEN_ENABLED: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
