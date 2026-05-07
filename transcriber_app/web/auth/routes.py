"""
Rutas de autenticación OAuth2 para TranscriberApp
"""

import os
import secrets
import base64
import hashlib
import json
import time
from urllib.parse import urlencode
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from transcriber_app.modules.logging.logging_config import setup_logging

logger = setup_logging("transcribeapp")

OAUTH_SESSIONS = {}

SESSION_EXPIRY_SECONDS = 300


def cleanup_expired_sessions():
    """Elimina sesiones OAuth expiradas (más de 5 minutos)"""
    current_time = time.time()
    expired_states = [
        state
        for state, data in OAUTH_SESSIONS.items()
        if current_time - data["created_at"] > SESSION_EXPIRY_SECONDS
    ]
    for state in expired_states:
        del OAUTH_SESSIONS[state]
    if expired_states:
        logger.info(f"[CLEANUP] Removed {len(expired_states)} expired OAuth sessions")


# Router
router = APIRouter(prefix="", tags=["auth"])

# Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = Jinja2Templates(directory=os.path.join(BASE_DIR, "..", "templates"))


def get_oauth_config():
    return {
        "oauth2_url": os.environ.get(
            "PUBLIC_OAUTH2_URL", "http://localhost:8080"
        ).rstrip("/"),
        "oauth2_internal_url": os.environ.get(
            "OAUTH2_URL", "http://localhost:8080"
        ).rstrip("/"),
        "client_id": os.environ.get("OAUTH2_CLIENT_ID", "transcriberapp"),
        "client_secret": os.environ.get("OAUTH2_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get(
            "PUBLIC_REDIRECT_URI", "http://localhost:9000/oauth/callback"
        ),
        "token_endpoint": os.environ.get("OAUTH2_TOKEN_ENDPOINT", "/oauth2/token"),
        "userinfo_endpoint": os.environ.get("OAUTH2_USERINFO_ENDPOINT", "/user/me"),
    }


def generate_code_verifier() -> str:
    random_bytes = secrets.token_bytes(32)
    verifier = base64.urlsafe_b64encode(random_bytes).decode("utf-8").rstrip("=")
    return verifier


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return challenge


@router.get("/login")
async def login_page(request: Request):
    if request.cookies.get("logged_in"):
        return RedirectResponse(url="/", status_code=302)
    config = get_oauth_config()
    return TEMPLATES.TemplateResponse(
        "login.html",
        {
            "request": request,
            "oauth2_url": config["oauth2_url"],
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
        },
    )


@router.post("/api/auth/oauth2/start")
async def start_oauth2_flow(request: Request):
    logger.info("=== START_OAUTH2_FLOW LLAMADO ===")
    try:
        if request.cookies.get("logged_in"):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Ya hay una sesión activa"},
            )

        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(16)
        config = get_oauth_config()

        logger.info(f"[OAUTH_START] STATE generado: {state}")

        state_data = {"s": state, "v": code_verifier}
        state_json = json.dumps(state_data)
        encoded_state = (
            base64.urlsafe_b64encode(state_json.encode()).decode().rstrip("=")
        )

        logger.info(f"[OAUTH_START] ENCODED_STATE: {encoded_state}")
        logger.info(
            f"[OAUTH_START] OAUTH_SESSIONS antes: {list(OAUTH_SESSIONS.keys())[:5]}"
        )

        params = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": "openid profile read write",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": encoded_state,
            "prompt": "login",
        }

        auth_url = f"{config['oauth2_url']}/oauth2/authorize?{urlencode(params)}"
        logger.info(f"[OAUTH_START] URL: {auth_url[:100]}...")

        OAUTH_SESSIONS[encoded_state] = {
            "code_verifier": code_verifier,
            "created_at": time.time(),
        }
        logger.info(
            f"[OAUTH_START] OAUTH_SESSIONS después: {list(OAUTH_SESSIONS.keys())[:5]}"
        )
        logger.info(f"[OAUTH_START] Session stored for state: {encoded_state[:30]}...")

        response = JSONResponse(
            content={"success": True, "authorization_url": auth_url}
        )

        return response
    except Exception as e:
        logger.error(f"[OAUTH_START] Error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    try:
        cleanup_expired_sessions()
        logger.info(f"[OAUTH_CALLBACK] Query params: {dict(request.query_params)}")

        code = request.query_params.get("code")
        error = request.query_params.get("error")
        state = request.query_params.get("state")

        if error:
            return TEMPLATES.TemplateResponse(
                "login.html", {"request": request, "error": f"Error OAuth: {error}"}
            )

        if not code:
            return TEMPLATES.TemplateResponse(
                "login.html", {"request": request, "error": "Código faltante"}
            )

        if not state:
            return TEMPLATES.TemplateResponse(
                "login.html", {"request": request, "error": "State faltante"}
            )

        session_data = OAUTH_SESSIONS.get(state)
        if not session_data:
            logger.warning(
                f"[OAUTH_CALLBACK] State {state[:30] if state else 'None'} no encontrado en sesiones"
            )
            logger.info(
                f"[OAUTH_CALLBACK] Claves disponibles: {list(OAUTH_SESSIONS.keys())[:5]}..."
            )
            return TEMPLATES.TemplateResponse(
                "login.html",
                {"request": request, "error": "Sesión expirada o inválida"},
            )

        code_verifier = session_data["code_verifier"]
        del OAUTH_SESSIONS[state]
        logger.info(
            f"[OAUTH_CALLBACK] Session retrieved and deleted for state: {state[:20]}..."
        )

        config = get_oauth_config()
        token_url = f"{config['oauth2_internal_url']}{config['token_endpoint']}"

        logger.info(f"[OAUTH_CALLBACK] Token URL: {token_url}")

        import httpx

        client_credentials = f"{config['client_id']}:{config['client_secret']}"
        basic_token = base64.b64encode(client_credentials.encode()).decode()

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": config["redirect_uri"],
                    "code_verifier": code_verifier,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_token}",
                },
            )

            logger.info(
                f"[OAUTH_CALLBACK] Token response status: {token_response.status_code}"
            )

            if token_response.status_code != 200:
                logger.error(f"[OAUTH_CALLBACK] Error: {token_response.text}")
                return TEMPLATES.TemplateResponse(
                    "login.html",
                    {"request": request, "error": "Error intercambiando código"},
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            userinfo_response = await client.get(
                f"{config['oauth2_internal_url']}{config['userinfo_endpoint']}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code == 200:
                user_info = userinfo_response.json()
            else:
                user_info = {"sub": "1", "email": "user@example.com", "name": "User"}

        response = RedirectResponse(url="/", status_code=302)
        is_secure = config["oauth2_url"].startswith("https")

        response.set_cookie(
            "logged_in",
            "true",
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,
        )
        response.set_cookie(
            "user_id",
            str(user_info.get("sub", 1)),
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,
        )
        response.set_cookie(
            "email",
            user_info.get("email", ""),
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,
        )
        response.set_cookie(
            "username",
            user_info.get("preferred_username", user_info.get("name", "user")),
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=86400,
        )

        logger.info("[OAUTH_CALLBACK] Login exitoso")
        return response
    except Exception as e:
        logger.error(f"[OAUTH_CALLBACK] Error: {e}", exc_info=True)
        return TEMPLATES.TemplateResponse(
            "login.html", {"request": request, "error": str(e)}
        )


@router.get("/api/auth/check")
async def check_auth(request: Request):
    logged_in = request.cookies.get("logged_in")
    if logged_in:
        return {
            "logged_in": True,
            "user_id": request.cookies.get("user_id"),
            "username": request.cookies.get("username"),
        }
    return {"logged_in": False}


@router.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    response = JSONResponse(content={"success": True})
    response.delete_cookie("logged_in")
    response.delete_cookie("user_id")
    response.delete_cookie("email")
    response.delete_cookie("username")
    return response


@router.get("/api/auth/userinfo")
async def userinfo(request: Request):
    """Obtiene información del usuario desde el token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "No token provided"})

    access_token = auth_header.replace("Bearer ", "")

    config = get_oauth_config()
    userinfo_url = f"{config['oauth2_internal_url']}{config['userinfo_endpoint']}"

    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            return JSONResponse(
                status_code=response.status_code,
                content={"error": "Failed to get userinfo"},
            )

        return JSONResponse(content=response.json())


@router.post("/api/auth/exchange-token")
async def exchange_token(request: Request, response: Response):
    try:
        data = await request.json()
        code = data.get("code")
        code_verifier = data.get("code_verifier")

        if not code or not code_verifier:
            return JSONResponse(
                status_code=400, content={"error": "code and code_verifier required"}
            )

        config = get_oauth_config()
        token_url = f"{config['oauth2_internal_url']}{config['token_endpoint']}"

        logger.info(f"[EXCHANGE_TOKEN] Client ID: {config['client_id']}")
        logger.info(f"[EXCHANGE_TOKEN] Redirect URI: {config['redirect_uri']}")
        logger.info(f"[EXCHANGE_TOKEN] Token URL: {token_url}")

        import httpx

        client_credentials = f"{config['client_id']}:{config['client_secret']}"
        basic_token = base64.b64encode(client_credentials.encode()).decode()

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": config["redirect_uri"],
                    "code_verifier": code_verifier,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {basic_token}",
                },
            )

            logger.info(f"[EXCHANGE_TOKEN] Response: {token_resp.status_code}")

            if token_resp.status_code != 200:
                return JSONResponse(
                    status_code=token_resp.status_code,
                    content={
                        "error": "Failed to exchange token",
                        "detail": token_resp.text,
                    },
                )

            tokens = token_resp.json()
            access_token = tokens.get("access_token")

            userinfo_response = await client.get(
                f"{config['oauth2_internal_url']}{config['userinfo_endpoint']}",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code == 200:
                user_info = userinfo_response.json()
            else:
                user_info = {
                    "sub": "1",
                    "email": "user@example.com",
                    "name": "User",
                    "preferred_username": "user",
                }

            is_secure = config["oauth2_url"].startswith("https")

            logger.info(f"[EXCHANGE_TOKEN] Setting cookies - secure: {is_secure}")

            response.set_cookie(
                key="logged_in",
                value="true",
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=86400,
                path="/",
            )
            response.set_cookie(
                key="user_id",
                value=str(user_info.get("sub", 1)),
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=86400,
                path="/",
            )
            response.set_cookie(
                key="email",
                value=user_info.get("email", ""),
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=86400,
                path="/",
            )
            response.set_cookie(
                key="username",
                value=user_info.get(
                    "preferred_username", user_info.get("name", "user")
                ),
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=86400,
                path="/",
            )

            logger.info(
                f"[EXCHANGE_TOKEN] Login exitoso para: "
                f"{user_info.get('preferred_username', user_info.get('name', 'user'))}"
            )

            return JSONResponse(
                content=tokens, status_code=200, headers=dict(response.headers)
            )

    except Exception as e:
        logger.error(f"[EXCHANGE_TOKEN] Error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
