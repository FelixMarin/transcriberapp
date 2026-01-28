# transcriber_app/web/api/background.py
import os
import subprocess
from pathlib import Path
from .emailer import send_email_with_attachment
import asyncio
from modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

# Diccionario opcional para consultar estado desde /status
JOB_STATUS = {}

def process_audio_job(job_id: str, nombre: str, modo: str, email: str):
    logger.info(f"[BACKGROUND JOB] Iniciando job {job_id} para archivo: {nombre} con modo: {modo} y email: {email}")
    try:
        JOB_STATUS[job_id] = "running"

        # Detectar si estamos dentro de Docker
        # /app existe solo dentro del contenedor
        if os.path.exists("/app"):
            cwd = "/app"
        else:
            # Directorio raíz del proyecto cuando se ejecuta localmente
            cwd = str(Path(__file__).resolve().parents[3])

        cmd = [
            "python3",
            "-m",
            "transcriber_app.main",
            "audio",
            nombre,
            modo
        ]

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            JOB_STATUS[job_id] = "error"
            print("Error ejecutando CLI:", result.stderr)
            return

        # Buscar archivo generado
        output_file = Path("outputs") / f"{nombre}_{modo}.md"

        if not output_file.exists():
            JOB_STATUS[job_id] = "error"
            print("No se encontró el archivo generado:", output_file)
            return

        # Enviar email con adjunto
        asyncio.run(send_email_with_attachment(
            to=email,
            subject=f"Transcripción lista: {nombre}",
            body="Adjunto encontrarás el archivo procesado.",
            attachment_path=output_file
        ))

        JOB_STATUS[job_id] = "done"

    except Exception as e:
        JOB_STATUS[job_id] = "error"
        logger.error(f"[BACKGROUND JOB] Error en job {job_id}: {e}")
