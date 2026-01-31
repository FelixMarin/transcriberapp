# transcriber_app/web/api/background.py

import os
import subprocess
from pathlib import Path
from .emailer import send_email_with_attachment
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

# Diccionario opcional para consultar estado desde /status
JOB_STATUS = {}


def process_audio_job(job_id: str, nombre: str, modo: str, email: str):
    logger.info(f"[BACKGROUND JOB] Iniciando job {job_id}")
    logger.info(f"[BACKGROUND JOB] Parámetros recibidos: nombre={nombre!r}, modo={modo!r}, email={email!r}")

    try:
        JOB_STATUS[job_id] = "running"

        # -----------------------------
        # 1. Determinar directorio de trabajo
        # -----------------------------
        logger.info("[BACKGROUND JOB] Determinando directorio de trabajo...")

        if os.path.exists("/app"):
            cwd = "/app"
            logger.info("[BACKGROUND JOB] Ejecutando dentro de Docker. cwd=/app")
        else:
            cwd = str(Path(__file__).resolve().parents[3])
            logger.info(f"[BACKGROUND JOB] Ejecutando localmente. cwd={cwd}")

        # -----------------------------
        # 2. Construir comando CLI
        # -----------------------------
        cmd = [
            "python3",
            "-m",
            "transcriber_app.main",
            "audio",
            nombre,
            modo
        ]

        logger.info(f"[BACKGROUND JOB] Comando a ejecutar: {cmd}")

        # -----------------------------
        # 3. Ejecutar proceso
        # -----------------------------
        logger.info("[BACKGROUND JOB] Ejecutando CLI...")

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )

        logger.info(f"[BACKGROUND JOB] CLI finalizada con returncode={result.returncode}")
        logger.info(f"[BACKGROUND JOB] STDOUT: {result.stdout!r}")
        logger.info(f"[BACKGROUND JOB] STDERR: {result.stderr!r}")

        if result.returncode == 3:
            JOB_STATUS[job_id] = "bad_audio"
            logger.error("[BACKGROUND JOB] Audio rechazado por mala calidad")
            return

        if result.returncode != 0:
            JOB_STATUS[job_id] = "error"
            logger.error(f"[BACKGROUND JOB] Error ejecutando CLI. returncode={result.returncode}")
            return

        # -----------------------------
        # 4. Verificar archivo generado
        # -----------------------------
        output_file = Path("outputs") / f"{nombre}_{modo}.md"
        logger.info(f"[BACKGROUND JOB] Buscando archivo generado: {output_file}")

        if not output_file.exists():
            JOB_STATUS[job_id] = "error"
            logger.error(f"[BACKGROUND JOB] Archivo no encontrado: {output_file}")
            return

        logger.info(f"[BACKGROUND JOB] Archivo encontrado correctamente: {output_file}")

        # -----------------------------
        # 5. Preparar envío de email
        # -----------------------------
        logger.info(
            f"[BACKGROUND JOB] Preparando envío de email: "
            f"to={email!r}, subject={f'Transcripción lista: {nombre}'!r}, "
            f"attachment={str(output_file)!r}"
        )

        # -----------------------------
        # 6. Enviar email
        # -----------------------------
        logger.info("[BACKGROUND JOB] Enviando email con adjunto...")

        send_email_with_attachment(
            to=email,
            subject=f"Transcripción lista: {nombre}",
            body="Adjunto encontrarás el archivo procesado.",
            attachment_path=str(output_file)
        )

        logger.info("[BACKGROUND JOB] Email enviado correctamente")

        # -----------------------------
        # 7. Finalizar job
        # -----------------------------
        JOB_STATUS[job_id] = "done"
        logger.info(f"[BACKGROUND JOB] Job {job_id} finalizado correctamente")

    except Exception as e:
        JOB_STATUS[job_id] = "error"
        logger.error(f"[BACKGROUND JOB] Error en job {job_id}: {e}", exc_info=True)
