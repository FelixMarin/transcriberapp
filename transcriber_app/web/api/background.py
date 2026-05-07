# transcriber_app/web/api/background.py

from transcriber_app.runner.orchestrator import Orchestrator, AudioValidationError
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber
from transcriber_app.modules.logging.logging_config import setup_logging
from pathlib import Path
import os
import glob

# Logging
logger = setup_logging("transcribeapp")

JOB_STATUS = {}


def process_audio_job(job_id: str, nombre: str, modo: str, email: str):
    logger.info(f"[BACKGROUND JOB] Iniciando job {job_id}")
    logger.info(f"[BACKGROUND JOB] Parámetros: nombre={nombre!r}, modo={modo!r}, email={email!r}")

    audio_path = None
    original_filename = None
    
    try:
        JOB_STATUS[job_id] = {"status": "running"}

        # Buscar el archivo con diferentes extensiones posibles
        audios_dir = Path("audios")
        logger.info(f"[BACKGROUND JOB] Buscando en: {audios_dir.absolute()}")
        
        # Listar todos los archivos en audios/
        if audios_dir.exists():
            all_files = list(audios_dir.glob("*"))
            logger.info(f"[BACKGROUND JOB] Archivos en audios/: {[f.name for f in all_files]}")
        
        # Buscar por nombre base sin extensión
        possible_extensions = [".m4a", ".mp4", ".webm", ".mp3", ".wav", ".aac", ".flac"]
        
        for ext in possible_extensions:
            temp_path = audios_dir / f"{nombre}{ext}"
            if temp_path.exists():
                audio_path = temp_path
                original_filename = f"{nombre}{ext}"
                logger.info(f"[BACKGROUND JOB] Audio encontrado: {audio_path}")
                break
        
        # Si no se encuentra, buscar cualquier archivo que contenga el nombre
        if not audio_path:
            for ext in possible_extensions:
                pattern = f"{nombre}*{ext}"
                matches = list(audios_dir.glob(pattern))
                if matches:
                    audio_path = matches[0]
                    original_filename = audio_path.name
                    logger.info(f"[BACKGROUND JOB] Audio encontrado por patrón: {audio_path}")
                    break

        if not audio_path:
            error_msg = f"Audio no encontrado para: {nombre}. Buscado en {audios_dir.absolute()}"
            logger.error(f"[BACKGROUND JOB] {error_msg}")
            JOB_STATUS[job_id] = {"status": "error", "error": error_msg}
            return

        # Verificar tamaño del archivo
        file_size = os.path.getsize(audio_path)
        logger.info(f"[BACKGROUND JOB] Tamaño del audio: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")

        # === USAR EL MISMO PIPELINE QUE EL CLI PERO SIN GUARDAR ARCHIVOS ===
        orchestrator = Orchestrator(
            receiver=AudioReceiver(),
            transcriber=GroqTranscriber(),
            formatter=OutputFormatter(),
            save_files=False
        )

        output_file, text, summary = orchestrator.run_audio(str(audio_path), modo)

        logger.info(f"[BACKGROUND JOB] Procesamiento en memoria completado para {nombre}")
        logger.info(f"[BACKGROUND JOB] Transcripción obtenida: {len(text)} caracteres")
        if text:
            logger.info(f"[BACKGROUND JOB] Primeros 100 caracteres: {text[:100]}")

        # Guardar resultados en el JOB_STATUS para que el frontend los recoja
        JOB_STATUS[job_id] = {
            "status": "done",
            "transcription": text,
            "markdown": summary
        }

        logger.info(f"[BACKGROUND JOB] Job {job_id} finalizado correctamente")

    except AudioValidationError as e:
        # Error específico de validación de audio
        validation_result = e.validation_result if e.validation_result else {}
        issues = validation_result.get("issues", [])
        warnings = validation_result.get("warnings", [])
        metadata = validation_result.get("metadata", {})

        # Construir mensaje detallado
        error_details = []
        if issues:
            error_details.extend(issues)
        if warnings:
            error_details.extend(warnings)

        error_message = str(e) if str(e) else "El audio no cumple los requisitos mínimos"

        JOB_STATUS[job_id] = {
            "status": "validation_error",
            "error": error_message,
            "validation_result": validation_result,
            "issues": issues,
            "warnings": warnings,
            "metadata": metadata
        }
        logger.error(f"[BACKGROUND JOB] Error de validación en job {job_id}: {error_message}")
        logger.error(f"[BACKGROUND JOB] Detalles: issues={issues}, warnings={warnings}")

    except Exception as e:
        JOB_STATUS[job_id] = {"status": "error", "error": str(e)}
        logger.error(f"[BACKGROUND JOB] Error en job {job_id}: {e}", exc_info=True)
        
    finally:
        # Eliminar el audio original (cualquier extensión)
        if audio_path and audio_path.exists():
            try:
                os.remove(audio_path)
                logger.info(f"[BACKGROUND JOB] Audio temporal eliminado: {audio_path}")
            except Exception as e:
                logger.warning(f"[BACKGROUND JOB] No se pudo eliminar el audio temporal {audio_path}: {e}")
        else:
            # Si no se encontró audio_path pero hay archivos en audios/, intentar limpiar
            try:
                audios_dir = Path("audios")
                if audios_dir.exists():
                    for ext in [".m4a", ".mp4", ".webm", ".mp3", ".wav", ".aac", ".flac"]:
                        pattern = f"{nombre}*{ext}"
                        for file_path in audios_dir.glob(pattern):
                            os.remove(file_path)
                            logger.info(f"[BACKGROUND JOB] Limpiado archivo huérfano: {file_path}")
            except Exception as e:
                logger.warning(f"[BACKGROUND JOB] Error limpiando archivos: {e}")