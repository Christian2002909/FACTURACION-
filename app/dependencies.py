from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.exceptions import http_401

bearer = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    from app.services.auth_service import decode_token
    payload = decode_token(credentials.credentials)
    if not payload:
        raise http_401()
    return payload
