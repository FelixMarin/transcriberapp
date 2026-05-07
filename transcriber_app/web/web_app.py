# transcriber_app/web/web_app.py
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse

from .api.routes import router as api_router
from .auth.routes import router as auth_router
from transcriber_app.config import APP_VERSION


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200 and path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response

print(">>> CARGANDO WEB_APP.PY REAL <<<")


def create_app() -> FastAPI:
    app = FastAPI(title="TranscriberApp Web")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://transcriber.nbes.blog",
            "https://oauth2.nbes.blog",
            "http://localhost:9000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Set-Cookie", "X-Login-Success"],
    )

    # API
    app.include_router(api_router, prefix="/api")

    # Auth routes (sin prefijo /api)
    app.include_router(auth_router)

    # Ruta absoluta al directorio static
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")

    # Servir archivos estáticos en /static (SIN transformaciones de contenido)
    app.mount("/static", NoCacheStaticFiles(directory=STATIC_DIR), name="static")

    # Ruta absoluta al directorio outputs
    OUTPUTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "outputs"))
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    print(">>> SERVING OUTPUTS FROM:", OUTPUTS_DIR)

    # Servir archivos .md generados por el backend
    app.mount("/api/resultados", StaticFiles(directory=OUTPUTS_DIR), name="resultados")

    # Ruta absoluta al directorio transcripts
    TRANSCRIPTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "transcripts"))
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    print(">>> SERVING TRANSCRIPTS FROM:", TRANSCRIPTS_DIR)

    # Servir archivos .txt de transcripciones
    app.mount(
        "/api/transcripciones",
        StaticFiles(directory=TRANSCRIPTS_DIR),
        name="transcripciones",
    )

    # Ruta explícita para /
    @app.get("/")
    async def root(request: Request):
        print(">>> EJECUTANDO ROOT <<<")
        # Verificar si está autenticado
        logged_in = request.cookies.get("logged_in")
        if not logged_in:
            # Redirigir a login
            return RedirectResponse(url="/login")

        index_path = os.path.join(STATIC_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Reemplazar placeholder de versión para cache busting
        html_content = html_content.replace("{{APP_VERSION}}", str(APP_VERSION))

        return HTMLResponse(content=html_content)

    return app


app = create_app()
