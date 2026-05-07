# transcriber_app/web/api/routes.py
import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
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

RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "/tmp/recordings")
UPLOADS_TEMP_DIR = os.getenv("UPLOADS_TEMP_DIR", "/tmp/audios_chunks")
Path(UPLOADS_TEMP_DIR).mkdir(exist_ok=True)

router = APIRouter(prefix="", tags=["auth"])


def check_auth(request: Request):
    """Verifica si el usuario está autenticado"""
    return request.cookies.get("logged_in") == "true"


@router.post("/upload-audio")
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...)
):
    """Recibe el audio grabado desde el navegador y lanza el procesamiento (subida simple, sin chunks)."""
    # Verificar autenticación
    if not check_auth(request):
        logger.warning(f"[UPLOAD AUDIO] Autenticación fallida para: {nombre}")
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    # Validación básica
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        logger.error(f"[UPLOAD AUDIO] Modo inválido recibido: {modo} para: {nombre}")
        raise HTTPException(status_code=400, detail="Modo inválido")

    # Carpeta donde guardas los audios
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)

    # Guardar archivo con su extensión original
    safe_name = nombre.lower()
    original_ext = Path(audio.filename).suffix.lower() if audio.filename else ".webm"

    if not original_ext:
        original_ext = ".webm"

    audio_path = audios_dir / f"{safe_name}{original_ext}"

    # Leer contenido y guardar
    audio_content = await audio.read()
    audio_size = len(audio_content)
    logger.info(f"[UPLOAD AUDIO] Iniciando subida simple:")
    logger.info(f"  Nombre: {nombre}")
    logger.info(f"  Tamaño: {(audio_size/1024/1024).toFixed(2)} MB")
    logger.info(f"  Extensión: {original_ext}")
    logger.info(f"  Ruta destino: {audio_path}")

    with audio_path.open("wb") as f:
        f.write(audio_content)

    saved_size = audio_path.stat().st_size
    logger.info(f"[UPLOAD AUDIO] Archivo guardado correctamente - tamaño: {(saved_size/1024/1024).toFixed(2)} MB")

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

    logger.info(f"[API ROUTE] Job {job_id} iniciado para audio: {nombre} (subida simple)")

    return {
        "status": "processing",
        "job_id": job_id,
        "message": "Audio recibido. Procesamiento iniciado."
    }


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
    extension: str = Form(...)
):
    """Recibe un chunk del archivo de audio y lo guarda temporalmente."""
    # Verificar autenticación
    if not check_auth(request):
        logger.warning(f"[CHUNK UPLOAD] Autenticación fallida para uploadId: {uploadId}")
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    # Validar modo
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        logger.error(f"[CHUNK UPLOAD] Modo inválido: {modo} para uploadId: {uploadId}")
        raise HTTPException(status_code=400, detail="Modo inválido")

    # Crear directorio para esta subida
    upload_dir = Path(UPLOADS_TEMP_DIR) / uploadId
    upload_dir.mkdir(exist_ok=True)

    # Guardar la extensión en metadata (solo en el primer chunk)
    if chunkIndex == 0:
        metadata_path = upload_dir / "metadata.txt"
        metadata_path.write_text(extension)
        logger.info(f"[CHUNK UPLOAD] Iniciando subida - uploadId: {uploadId}, nombre: {nombre}, total chunks: {totalChunks}, extensión: .{extension}")

    # Guardar el chunk
    chunk_path = upload_dir / f"chunk_{chunkIndex:06d}"
    chunk_size = 0
    with chunk_path.open("wb") as f:
        # Copiar contenido y contar bytes
        shutil.copyfileobj(chunk.file, f)
        chunk_size = chunk_path.stat().st_size

    logger.info(f"[CHUNK UPLOAD] Chunk {chunkIndex + 1}/{totalChunks} recibido - tamaño: {chunk_size / (1024*1024):.2f} MB - ruta: {chunk_path}")

    return {
        "status": "chunk_received",
        "chunkIndex": chunkIndex,
        "uploadId": uploadId
    }


@router.post("/upload-complete")
async def upload_complete(
    request: Request,
    background_tasks: BackgroundTasks,
    uploadId: str = Form(...),
    nombre: str = Form(...),
    modo: str = Form(...),
    email: str = Form(...)
):
    """Ensambla todos los chunks y lanza el procesamiento."""
    # Verificar autenticación
    if not check_auth(request):
        logger.warning(f"[UPLOAD COMPLETE] Autenticación fallida para uploadId: {uploadId}")
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    # Validar modo
    if modo not in ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]:
        logger.error(f"[UPLOAD COMPLETE] Modo inválido: {modo} para uploadId: {uploadId}")
        raise HTTPException(status_code=400, detail="Modo inválido")

    upload_dir = Path(UPLOADS_TEMP_DIR) / uploadId

    if not upload_dir.exists():
        logger.error(f"[UPLOAD COMPLETE] Upload no encontrado: {uploadId}")
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    # Buscar todos los chunks ordenados
    chunk_files = sorted(upload_dir.glob("chunk_*"), key=lambda p: int(p.stem.split("_")[1]))

    if not chunk_files:
        logger.error(f"[UPLOAD COMPLETE] No se encontraron chunks en: {upload_dir}")
        raise HTTPException(status_code=400, detail="No se encontraron chunks")

    logger.info(f"[UPLOAD COMPLETE] Ensamblando {len(chunk_files)} chunks para uploadId: {uploadId}, nombre: {nombre}")

    # Determinar extensión desde metadata
    metadata_path = upload_dir / "metadata.txt"
    extension = "webm"  # default
    if metadata_path.exists():
        extension = metadata_path.read_text().strip()
        logger.info(f"[UPLOAD COMPLETE] Extensión detectada: .{extension}")
    else:
        logger.warning(f"[UPLOAD COMPLETE] No se encontró metadata, usando extensión por defecto: .{extension}")

    # Crear directorio audios si no existe
    audios_dir = Path("audios")
    audios_dir.mkdir(exist_ok=True)

    safe_name = nombre.lower()
    audio_path = audios_dir / f"{safe_name}.{extension}"

    # Calcular tamaño total de chunks
    total_chunks_size = sum(f.stat().st_size for f in chunk_files)
    logger.info(f"[UPLOAD COMPLETE] Tamaño total de chunks: {total_chunks_size / (1024*1024):.2f} MB")

    # Ensamblar archivo completo
    logger.info(f"[UPLOAD COMPLETE] Iniciando ensamblado en: {audio_path}")
    with audio_path.open("wb") as outfile:
        for idx, chunk_file in enumerate(chunk_files):
            with chunk_file.open("rb") as infile:
                shutil.copyfileobj(infile, outfile)
            if (idx + 1) % 10 == 0 or idx == len(chunk_files) - 1:
                logger.info(f"[UPLOAD COMPLETE] Progreso ensamblado: {idx + 1}/{len(chunk_files)} chunks")

    final_size = audio_path.stat().st_size
    logger.info(f"[UPLOAD COMPLETE] Archivo ensamblado correctamente - tamaño final: {final_size / (1024*1024):.2f} MB - ruta: {audio_path}")

    # Limpiar chunks temporales
    try:
        shutil.rmtree(upload_dir)
        logger.info(f"[UPLOAD COMPLETE] Chunks temporales eliminados: {upload_dir}")
    except Exception as e:
        logger.warning(f"[UPLOAD COMPLETE] Error eliminando directorio temporal {upload_dir}: {e}")

    # Crear ID de trabajo
    job_id = str(uuid.uuid4())

    # Lanzar proceso en background
    logger.info(f"[UPLOAD COMPLETE] Lanzando job {job_id} para audio: {nombre} (modo: {modo})")
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


@router.post("/upload-cancel")
async def upload_cancel(
    request: Request,
    uploadId: str = Form(...)
):
    """Cancela una subida en progreso y elimina los chunks temporales."""
    # Verificar autenticación
    if not check_auth(request):
        logger.warning(f"[UPLOAD CANCEL] Autenticación fallida para uploadId: {uploadId}")
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    upload_dir = Path(UPLOADS_TEMP_DIR) / uploadId

    if not upload_dir.exists():
        logger.warning(f"[UPLOAD CANCEL] Upload no encontrado: {uploadId}")
        raise HTTPException(status_code=404, detail="Upload no encontrado")

    try:
        shutil.rmtree(upload_dir)
        logger.info(f"[UPLOAD CANCEL] Chunks eliminados para uploadId: {uploadId}")
        return {
            "status": "cancelled",
            "uploadId": uploadId,
            "message": "Subida cancelada y chunks eliminados"
        }
    except Exception as e:
        logger.error(f"[UPLOAD CANCEL] Error eliminando {upload_dir}: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar chunks")


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job_data = JOB_STATUS.get(job_id, "unknown")

    # Log detallado del estado
    if isinstance(job_data, dict):
        status = job_data.get("status", "unknown")
        logger.info(f"[STATUS] Consulta para job {job_id} - estado actual: {status}")
        return job_data

    logger.info(f"[STATUS] Consulta para job {job_id} - estado: {job_data}")
    return {"job_id": job_id, "status": job_data}


@router.post("/chat/stream")
async def chat_stream(request: Request, payload: dict):
    # Verificar autenticación
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")

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
    # Verificar cualquier extensión común
    for ext in [".webm", ".mp3", ".wav", ".m4a", ".mp4"]:
        filename = f"{name}{ext}"
        if os.path.exists(os.path.join(RECORDINGS_DIR, filename)):
            return {"exists": True, "extension": ext}
    return {"exists": False}


@router.post("/process-existing")
async def process_existing(
    request: Request,
    nombre: str = Form(...),
    modo: str = Form(...),
    transcription: str = Form(None)
):
    # Verificar autenticación
    if not check_auth(request):
        raise HTTPException(status_code=401, detail="Autenticación requerida")

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
