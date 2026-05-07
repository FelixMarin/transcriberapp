"""
Dependencias de autenticación para FastAPI
Maneja la sesión y protección de rutas
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from .service import get_auth_service

# Almacén en memoria para sesiones (en producción usar Redis o similar)
SESSIONS: dict = {}


def create_session(user_id: int, user_data: dict) -> str:
    """Crea una sesión y devuelve el token"""
    auth_service = get_auth_service()
    token = auth_service.create_token(user_id)
    if token:
        SESSIONS[token] = {
            "user_id": user_id,
            "user_data": user_data
        }
    return token


def get_session(token: str) -> Optional[dict]:
    """Obtiene una sesión por token"""
    return SESSIONS.get(token)


def delete_session(token: str) -> bool:
    """Elimina una sesión"""
    if token in SESSIONS:
        del SESSIONS[token]
        return True
    return False


def get_current_user(request: Request) -> Optional[dict]:
    """Obtiene el usuario actual desde la cookie de sesión"""
    token = request.cookies.get("session_token")
    if not token:
        return None

    session = get_session(token)
    if session:
        return session.get("user_data")
    return None


def require_auth(request: Request):
    """Decorador/función que requiere autenticación"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def is_authenticated(request: Request) -> bool:
    """Verifica si el usuario está autenticado"""
    return get_current_user(request) is not None
