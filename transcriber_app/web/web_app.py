import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .api.routes import router as api_router

print(">>> CARGANDO WEB_APP.PY REAL <<<")

def create_app() -> FastAPI:
    app = FastAPI(title="TranscriberApp Web")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API
    app.include_router(api_router, prefix="/api")

    # Ruta absoluta al directorio static
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")

    # Servir archivos estáticos en /static
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # Ruta explícita para /
    @app.get("/")
    async def root():
        print(">>> EJECUTANDO ROOT <<<")
        index_path = os.path.join(STATIC_DIR, "index.html")
        return FileResponse(index_path)

    return app


app = create_app()
