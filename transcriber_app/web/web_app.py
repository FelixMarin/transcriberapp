from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="TranscriberApp Web")

    # CORS (por si accedes desde otra IP/puerto)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # si quieres, luego lo restringimos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rutas API (upload, process, status...)
    app.include_router(api_router, prefix="/api")

    # Servir archivos estáticos (index.html, JS, CSS)
    app.mount(
        "/",
        StaticFiles(directory="transcriber_app/web/static", html=True),
        name="static",
    )

    return app


app = create_app()
