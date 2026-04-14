"""
Rate limiting — FacturaPY
Protección contra abuso de API: fuerza bruta, spam de facturas, etc.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app: FastAPI):
    """Registra el limiter y el handler de error 429."""
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intenta de nuevo más tarde."},
        )
