# transcriber_app/web/api/routes.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from transcriber_app.modules.ai.ai_manager import AIManager
from transcriber_app.runner.orchestrator import Orchestrator
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber
from fastapi.responses import FileResponse
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
    safe_name = nombre.lower()
    audio_path = audios_dir / f"{safe_name}.mp3"
    with audio_path.open("wb") as f:
        f.write(await audio.read())

    # Crear ID de trabajo
    job_id = str(uuid.uuid4())

    # Lanzar proceso en background
    background_tasks.add_task(
        process_audio_job,
        job_id=job_id,
        nombre=safe_name,
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
    job_data = JOB_STATUS.get(job_id, "unknown")

    if isinstance(job_data, dict):
        return job_data

    return {"job_id": job_id, "status": job_data}


@router.post("/chat/stream")
async def chat_stream(payload: dict):
    message = payload.get("message", "")
    mode = payload.get("mode", "default")

    agent = AIManager.get_agent(mode)

    async def chat_stream_gen():
        try:
            logger.info(f"[CHAT STREAM] Iniciando stream para mensaje: {message[:50]}...")
            # agent.run(..., stream=True) devuelve un generador
            for chunk in agent.run(message, stream=True):
                if chunk:
                    yield chunk
            logger.info("[CHAT STREAM] Stream finalizado con éxito")
        except Exception as e:
            logger.error(f"[CHAT STREAM] Error en generador: {e}")
            yield f"\n[Error en servidor: {str(e)}]"

    return StreamingResponse(chat_stream_gen(), media_type="text/plain")


@router.get("/check-name")
def check_name(name: str):
    filename = f"{name}.mp3"
    exists = os.path.exists(os.path.join(RECORDINGS_DIR, filename))
    return {"exists": exists}


@router.post("/process-existing")
async def process_existing(
    nombre: str = Form(...),
    modo: str = Form(...),
    transcription: str = Form(None)
):
    text = None
    transcript_path = Path("transcripts") / f"{nombre}.txt"

    if transcription:
        text = transcription
        logger.info(f"[API ROUTE] Reutilizando transcripción recibida vía Form para: {nombre}")
    elif transcript_path.exists():
        text = transcript_path.read_text(encoding="utf-8")
        logger.info(f"[API ROUTE] Reutilizando transcripción desde archivo para: {nombre}")
    else:
        raise HTTPException(status_code=404, detail="Transcripción no encontrada (ni en Form ni en disco)")

    # Usar el mismo pipeline que CLI pero sin guardar
    orchestrator = Orchestrator(
        receiver=AudioReceiver(),
        transcriber=GroqTranscriber(),
        formatter=OutputFormatter(),
        save_files=False
    )

    # 1. Resumir con Gemini
    summary_output = AIManager.summarize(text, modo)

    # 2. Guardar métricas (SIEMPRE se guardan)
    orchestrator.formatter.save_metrics(nombre, summary_output, modo)

    return {
        "status": "done",
        "mode": modo,
        "markdown": summary_output,
        "transcription": text
    }


@router.get("/transcripciones/{filename}")
def get_transcription(filename: str):
    path = Path("transcripts") / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path, media_type="text/plain")


@router.get("/resultados/{filename}")
def get_result(filename: str):
    path = Path("outputs") / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(path, media_type="text/markdown")
