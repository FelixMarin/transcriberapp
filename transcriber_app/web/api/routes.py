# transcriber_app/web/api/routes.py
import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from transcriber_app.modules.ai.ai_manager import AIManager
from transcriber_app.modules.ai.gemini.agents import chat_agent
from transcriber_app.runner.orchestrator import Orchestrator
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber
from transcriber_app.web.api.background import process_audio_job, JOB_STATUS
from transcriber_app.modules.logging.logging_config import setup_logging

logger = setup_logging("transcribeapp")

RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "/tmp/recordings")
UPLOADS_TEMP_DIR = os.getenv("UPLOADS_TEMP_DIR", "/tmp/audios_chunks")
Path(UPLOADS_TEMP_DIR).mkdir(exist_ok=True)

router = APIRouter(prefix="", tags=["auth"])


def check_auth(request: Request):
    return request.cookies.get("logged_in") == "true"


@router.post("/upload-audio")
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...),
):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        raise HTTPException(status_code=400, detail="Modo inválido")
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)
    safe_name = nombre.lower()
    if '.' in safe_name:
        safe_name = safe_name.rsplit('.', 1)[0]
    original_ext = Path(audio.filename).suffix.lower() if audio.filename else ".webm"
    if not original_ext:
        original_ext = ".webm"
    audio_path = audios_dir / f"{safe_name}{original_ext}"
    audio_content = await audio.read()
    audio_size = len(audio_content)
    logger.info("[UPLOAD AUDIO] Iniciando subida simple")
    logger.info(f"  Nombre: {nombre}")
    logger.info(f"  Tamaño: {audio_size/1024/1024:.2f} MB")
    logger.info(f"  Extensión: {original_ext}")
    logger.info(f"  Ruta destino: {audio_path}")
    with audio_path.open("wb") as f:
        f.write(audio_content)
    saved_size = audio_path.stat().st_size
    logger.info(f"[UPLOAD AUDIO] Archivo guardado correctamente - tamaño: {saved_size/1024/1024:.2f} MB")
    job_id = str(uuid.uuid4())
    background_tasks.add_task(process_audio_job, job_id=job_id, nombre=safe_name, modo=modo, email=email)
    logger.info(f"[API ROUTE] Job {job_id} iniciado para audio: {nombre} (subida simple)")
    return {"status": "processing", "job_id": job_id, "message": "Audio recibido. Procesamiento iniciado."}


@router.post("/upload-chunk")
async def upload_chunk(
    request: Request,
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    uploadId: str = Form(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...),
    extension: str = Form(...),
):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        raise HTTPException(status_code=400, detail="Modo inválido")
    uploads_temp_dir = Path(UPLOADS_TEMP_DIR)
    upload_dir = uploads_temp_dir / uploadId
    upload_dir.mkdir(parents=True, exist_ok=True)
    if chunkIndex == 0:
        (upload_dir / "metadata.txt").write_text(extension)
    (upload_dir / f"chunk_{chunkIndex:06d}").write_bytes(await chunk.read())
    logger.info(f"[CHUNK UPLOAD] Chunk {chunkIndex + 1}/{totalChunks} recibido")
    return {"status": "chunk_received", "chunkIndex": chunkIndex, "uploadId": uploadId}


@router.post("/upload-complete")
async def upload_complete(
    request: Request,
    background_tasks: BackgroundTasks,
    uploadId: str = Form(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...),
):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        raise HTTPException(status_code=400, detail="Modo inválido")
    uploads_temp_dir = Path(UPLOADS_TEMP_DIR)
    upload_dir = uploads_temp_dir / uploadId
    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Upload no encontrado")
    chunk_files = sorted(upload_dir.glob("chunk_*"), key=lambda p: int(p.stem.split("_")[1]))
    if not chunk_files:
        raise HTTPException(status_code=400, detail="No se encontraron chunks")
    metadata_path = upload_dir / "metadata.txt"
    extension = metadata_path.read_text().strip() if metadata_path.exists() else "webm"
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)
    safe_name = nombre.lower()
    if '.' in safe_name:
        safe_name = safe_name.rsplit('.', 1)[0]
    audio_path = audios_dir / f"{safe_name}.{extension}"
    logger.info(f"[UPLOAD COMPLETE] Ensamblando {len(chunk_files)} chunks: {uploadId}")
    with audio_path.open("wb") as outfile:
        for chunk_file in chunk_files:
            outfile.write(chunk_file.read_bytes())
    try:
        shutil.rmtree(upload_dir)
        logger.info(f"[UPLOAD COMPLETE] Limpiado: {upload_dir}")
    except Exception as e:
        logger.warning(f"[UPLOAD COMPLETE] Error limpiando {upload_dir}: {e}")
    job_id = str(uuid.uuid4())
    background_tasks.add_task(process_audio_job, job_id=job_id, nombre=safe_name, modo=modo, email=email)
    logger.info(f"[API ROUTE] Job {job_id} iniciado para: {nombre}")
    return {"status": "processing", "job_id": job_id, "message": "Audio recibido. Procesamiento iniciado."}


@router.post("/upload-cancel")
async def upload_cancel(request: Request, uploadId: str = Form(...)):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    upload_dir = Path(UPLOADS_TEMP_DIR) / uploadId
    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="Upload no encontrado")
    shutil.rmtree(upload_dir)
    logger.info(f"[UPLOAD CANCEL] Limpiado: {uploadId}")
    return {"status": "cancelled", "uploadId": uploadId, "message": "Upload cancelado."}


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job_data = JOB_STATUS.get(job_id, "unknown")
    if isinstance(job_data, dict):
        return job_data
    return {"job_id": job_id, "status": job_data}


@router.post("/chat/stream")
async def chat_stream(request: Request, payload: dict):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    message = payload.get("message", "")
    transcripcion = payload.get("transcripcion", "")
    resumen = payload.get("resumen", "")
    history = payload.get("history", [])  # [{"role": "user"|"assistant", "content": "..."}]

    context_block = ""
    if transcripcion:
        context_block += f"## Transcripción original\n{transcripcion}\n\n"
    if resumen:
        context_block += f"## Análisis procesado\n{resumen}\n\n"

    # Build the full prompt: context + history + current question
    history_block = ""
    for turn in history[:-1]:  # exclude the current message (last user turn)
        role = "Usuario" if turn.get("role") == "user" else "Asistente"
        history_block += f"**{role}:** {turn.get('content', '')}\n\n"

    full_prompt = ""
    if context_block:
        full_prompt += f"{context_block}---\n\n"
    if history_block:
        full_prompt += f"## Historial de conversación\n{history_block}---\n\n"
    full_prompt += f"## Pregunta actual\n{message}"

    async def chat_stream_gen():
        try:
            for chunk in chat_agent.run(full_prompt, stream=True):
                if chunk:
                    yield chunk
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    return StreamingResponse(chat_stream_gen(), media_type="text/plain")


@router.get("/check-name")
def check_name(name: str):
    for ext in [".webm", ".mp3", ".wav", ".m4a", ".mp4"]:
        path = Path(RECORDINGS_DIR) / f"{name}{ext}"
        if path.exists():
            return {"exists": True, "extension": ext}
    return {"exists": False}


@router.post("/process-existing")
async def process_existing(
    request: Request,
    nombre: str = Form(...),
    modo: str = Form(...),
    transcription: str = Form(None),
):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    text = transcription
    if not text:
        transcript_path = Path("transcripts") / f"{nombre}.txt"
        if transcript_path.exists():
            text = transcript_path.read_text(encoding="utf-8")
        else:
            raise HTTPException(status_code=404, detail="Transcripción no encontrada")
    orchestrator = Orchestrator(AudioReceiver(), GroqTranscriber(), OutputFormatter(), save_files=False)
    summary_output = AIManager.summarize(text, modo)
    orchestrator.formatter.save_metrics(nombre, summary_output, modo)
    return {"status": "done", "mode": modo, "markdown": summary_output, "transcription": text}


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
