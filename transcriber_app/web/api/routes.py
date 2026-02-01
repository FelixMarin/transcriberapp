# transcriber_app/web/api/routes.py
import os
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pathlib import Path
from transcriber_app.modules.ai.ai_manager import AIManager, log_agent_result
import uuid

from .background import process_audio_job
from .background import JOB_STATUS
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

RECORDINGS_DIR = "recordings"

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


@router.post("/chat/stream")
async def chat_stream(payload: dict):
    message = payload.get("message", "")
    mode = payload.get("mode", "default")

    agent = AIManager.get_agent(mode)
    result = agent.run(message)
    log_agent_result(result)

    return {"response": result.content}


@router.get("/check-name")
def check_name(name: str):
    filename = f"{name}.mp3"
    exists = os.path.exists(os.path.join(RECORDINGS_DIR, filename))
    return {"exists": exists}


@router.post("/process-existing")
async def process_existing(
    nombre: str = Form(...),
    modo: str = Form(...)
):
    transcript_path = Path("transcripts") / f"{nombre}.txt"

    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcripción no encontrada")

    text = transcript_path.read_text(encoding="utf-8")

    agent = AIManager.get_agent(modo)
    result = agent.run(text)
    log_agent_result(result)

    return {
        "status": "done",
        "mode": modo,
        "content": result.content
    }
