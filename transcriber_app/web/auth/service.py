"""
Servicio de autenticación para TranscriberApp
Implementación que usa credenciales de entorno
"""
import os
import secrets
from typing import Tuple, Optional, Dict
from transcriber_app.modules.logging.logging_config import setup_logging

logger = setup_logging("transcribeapp")


class AuthService:
    """Servicio de autenticación básico con credenciales de entorno"""

    def __init__(self):
        self._valid_user = os.environ.get("APP_USER", "admin")
        self._valid_password = os.environ.get("APP_PASSWORD", "admin123")
        self._tokens: Dict[str, Dict] = {}
        logger.info(f"[AUTH SERVICE] Inicializado con usuario: {self._valid_user}")

    def login(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Inicia sesión con email y password

        Args:
            email: Email del usuario
            password: Contraseña del usuario

        Returns:
            (success, user_data)
        """
        logger.info(f"[AUTH SERVICE] Intento de login para: {email}")

        if email == self._valid_user and password == self._valid_password:
            user_data = {
                "id": 1,
                "email": email,
                "username": email,
                "role": "admin"
            }
            logger.info(f"[AUTH SERVICE] Login exitoso para: {email}")
            return True, user_data

        logger.warning(f"[AUTH SERVICE] Credenciales incorrectas para: {email}")
        return False, None

    def logout(self, user_id: int) -> bool:
        """Cierra sesión"""
        self._tokens = {k: v for k, v in self._tokens.items() if v.get("user_id") != user_id}
        logger.info(f"[AUTH SERVICE] Logout para user_id: {user_id}")
        return True

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifica un token de autenticación"""
        if token in self._tokens:
            token_data = self._tokens[token]
            return token_data.get("user_data")
        return None

    def refresh_token(self, token: str) -> Optional[str]:
        """Refresca un token de autenticación"""
        if token in self._tokens:
            # Generar nuevo token
            new_token = secrets.token_urlsafe(32)
            user_data = self._tokens[token].get("user_data")
            self._tokens[new_token] = {
                "user_id": user_data.get("id"),
                "user_data": user_data
            }
            # Eliminar token antiguo
            del self._tokens[token]
            return new_token
        return None

    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Obtiene los datos del usuario desde un token"""
        return self.verify_token(token)

    def create_token(self, user_id: int) -> Optional[str]:
        """Crea un token para un usuario"""
        token = secrets.token_urlsafe(32)
        user_data = {
            "id": user_id,
            "role": "admin"
        }
        self._tokens[token] = {
            "user_id": user_id,
            "user_data": user_data
        }
        logger.info(f"[AUTH SERVICE] Token creado para user_id: {user_id}")
        return token


# Instancia global del servicio
_auth_service = None


def get_auth_service() -> AuthService:
    """Obtiene la instancia global del servicio de autenticación"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
