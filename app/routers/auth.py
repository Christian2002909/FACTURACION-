import logging
from fastapi import APIRouter, Depends, Request
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import authenticate, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import http_401
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Autentica al usuario y retorna tokens JWT (acceso + refresco).",
    responses={
        200: {"description": "Login exitoso, retorna tokens"},
        401: {"description": "Credenciales inválidas"},
        429: {"description": "Demasiados intentos de login"},
    },
)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    if not authenticate(body.username, body.password):
        raise http_401()
    data = {"sub": body.username}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refrescar token",
    description="Genera nuevos tokens JWT a partir de un refresh token válido.",
    responses={
        200: {"description": "Tokens renovados exitosamente"},
        401: {"description": "Refresh token inválido o expirado"},
    },
)
@limiter.limit("20/minute")
def refresh(request: Request, body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise http_401()
    data = {"sub": payload["sub"]}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )
