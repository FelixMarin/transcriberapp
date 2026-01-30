#transcriber_app/web/api/routes.py
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from .models import ChatRequest
from pathlib import Path
from ...modules.gemini_client import chat_about_transcript, stream_chat_about_transcript
import uuid

from .background import process_audio_job
from .background import JOB_STATUS
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

router = APIRouter()

@router.post("/upload-audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...)
):
    logger.info(f"[API ROUTE] Recibido audio: {nombre} con modo: {modo} para email: {email}")
    """
    Recibe el audio grabado desde el navegador y lanza el procesamiento.
    """

    # Validación básica
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        logger.error(f"[API ROUTE] Modo inválido recibido: {modo}")
        raise HTTPException(status_code=400, detail="Modo inválido")

    # Carpeta donde guardas los audios
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)

    # Guardar archivo
    audio_path = audios_dir / f"{nombre}.mp3"
    with audio_path.open("wb") as f:
        f.write(await audio.read())

    # Crear ID de trabajo
    job_id = str(uuid.uuid4())

    # Lanzar proceso en background
    background_tasks.add_task(
        process_audio_job,
        job_id=job_id,
        nombre=nombre,
        modo=modo,
        email=email
    )

    logger.info(f"[API ROUTE] Job {job_id} iniciado para audio: {nombre}")
    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Audio recibido. Procesamiento iniciado."
    }

@router.get("/status/{job_id}")
def get_status(job_id: str):
    logger.info(f"[API ROUTE] Consultando estado del job: {job_id}")
    status = JOB_STATUS.get(job_id, "unknown")
    return {"job_id": job_id, "status": status}

@router.post("/chat")
async def chat_endpoint(payload: ChatRequest):
    respuesta = await chat_about_transcript(
        transcripcion=payload.transcripcion,
        resumen=payload.resumen,
        pregunta=payload.pregunta,
        historial=[m.dict() for m in payload.historial],
    )
    return {"respuesta": respuesta}

@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    async def event_generator():
        async for chunk in stream_chat_about_transcript(
            payload.transcripcion,
            payload.resumen,
            payload.pregunta,
            [m.dict() for m in payload.historial]
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain")
