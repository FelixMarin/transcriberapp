# transcriber_app/web/api/background.py

from transcriber_app.runner.orchestrator import Orchestrator
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber
from transcriber_app.modules.logging.logging_config import setup_logging
from pathlib import Path
import os

# Logging
logger = setup_logging("transcribeapp")

JOB_STATUS = {}


def process_audio_job(job_id: str, nombre: str, modo: str, email: str):
    logger.info(f"[BACKGROUND JOB] Iniciando job {job_id}")
    logger.info(f"[BACKGROUND JOB] Parámetros: nombre={nombre!r}, modo={modo!r}, email={email!r}")

    try:
        JOB_STATUS[job_id] = {"status": "running"}

        # Buscar el archivo con diferentes extensiones posibles
        audio_path = None
        for ext in [".m4a", ".mp4", ".webm", ".mp3", ".wav"]:
            temp_path = Path("audios") / f"{nombre}{ext}"
            if temp_path.exists():
                audio_path = temp_path
                break

        if not audio_path:
            JOB_STATUS[job_id] = {"status": "error"}
            logger.error(f"[BACKGROUND JOB] Audio no encontrado para: {nombre}")
            return

        # === USAR EL MISMO PIPELINE QUE EL CLI PERO SIN GUARDAR ARCHIVOS ===
        orchestrator = Orchestrator(
            receiver=AudioReceiver(),
            transcriber=GroqTranscriber(),
            formatter=OutputFormatter(),
            save_files=False
        )

        output_file, text, summary = orchestrator.run_audio(str(audio_path), modo)

        logger.info(f"[BACKGROUND JOB] Procesamiento en memoria completado para {nombre}")

        # Guardar resultados en el JOB_STATUS para que el frontend los recoja
        JOB_STATUS[job_id] = {
            "status": "done",
            "transcription": text,
            "markdown": summary
        }

        logger.info(f"[BACKGROUND JOB] Job {job_id} finalizado correctamente")

    except Exception as e:
        JOB_STATUS[job_id] = {"status": "error", "error": str(e)}
        logger.error(f"[BACKGROUND JOB] Error en job {job_id}: {e}", exc_info=True)
    finally:
        # Borrar el audio original siempre
        try:
            audio_path = Path("audios") / f"{nombre}.webm"
            if audio_path.exists():
                os.remove(audio_path)
                logger.info(f"[BACKGROUND JOB] Audio temporal eliminado: {audio_path}")
        except Exception as e:
            logger.warning(f"[BACKGROUND JOB] No se pudo eliminar el audio temporal: {e}")
