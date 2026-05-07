"""
Casos de uso de autenticación para TranscriberApp
"""
from typing import Optional, Dict, Tuple
from .service import get_auth_service


class LoginUseCase:
    """Caso de uso para iniciar sesión"""

    def __init__(self):
        self._auth_service = get_auth_service()

    def execute(self, email: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """
        Inicia sesión con email y password

        Args:
            email: Email del usuario
            password: Contraseña del usuario

        Returns:
            Tupla (success, user_data)
        """
        return self._auth_service.login(email, password)

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifica un token de autenticación"""
        return self._auth_service.verify_token(token)

    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Obtiene el usuario desde un token"""
        return self._auth_service.get_user_from_token(token)


class LogoutUseCase:
    """Caso de uso para cerrar sesión"""

    def __init__(self):
        self._auth_service = get_auth_service()

    def execute(self, user_id: int) -> bool:
        """
        Cierra sesión del usuario

        Args:
            user_id: ID del usuario

        Returns:
            True si el logout fue exitoso
        """
        return self._auth_service.logout(user_id)


# Instancias globales de casos de uso
_login_use_case = None
_logout_use_case = None


def get_login_use_case() -> LoginUseCase:
    """Obtiene la instancia global del caso de uso de login"""
    global _login_use_case
    if _login_use_case is None:
        _login_use_case = LoginUseCase()
    return _login_use_case


def get_logout_use_case() -> LogoutUseCase:
    """Obtiene la instancia global del caso de uso de logout"""
    global _logout_use_case
    if _logout_use_case is None:
        _logout_use_case = LogoutUseCase()
    return _logout_use_case
