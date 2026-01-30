# transcriber_app/modules/audio_downloader.py
import yt_dlp
import os
import re
import uuid
import subprocess
import json
from transcriber_app.modules.logging.logging_config import setup_logging
from pathlib import Path
import sys

# Logging
logger = setup_logging("transcribeapp")

def extract_video_id(url: str) -> str:
    """Extrae un ID del vídeo si es posible, si no genera un UUID."""
    patterns = [
        r"v=([A-Za-z0-9_-]+)",          # YouTube normal
        r"youtu\.be/([A-Za-z0-9_-]+)",  # YouTube corto
        r"/video/([A-Za-z0-9_-]+)",     # TikTok / Vimeo / etc.
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return str(uuid.uuid4())


def get_audio_duration(path: str) -> float:
    """Devuelve la duración en segundos usando ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def download_audio(url: str, output_dir: str = "./audios", max_duration: int = 9000) -> str:
    """
    Descarga solo el audio de un vídeo y lo convierte a MP3.
    Devuelve la ruta final del archivo.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    audio_id = extract_video_id(url)
    final_path = os.path.join(output_dir, f"{audio_id}.mp3")

    # Si ya existe, devolverlo
    if os.path.exists(final_path):
        logger.info(f"[AUDIO] Ya existe en caché: {final_path}")
        return final_path

    # 1. Extraer metadata primero
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration")

        if duration:
            logger.info(f"[AUDIO] Duración detectada: {duration/60:.1f} min")
            if duration > max_duration:
                raise ValueError(
                    f"❌ El audio dura {duration/60:.1f} min, supera el límite de {max_duration/60} min."
                )

    # 2. Descargar solo audio
    outtmpl = os.path.join(output_dir, f"{audio_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestaudio/best',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    logger.info(f"[AUDIO] Descargando audio desde: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # 3. Si no había duración, comprobar ahora
    if duration is None:
        try:
            duration = get_audio_duration(final_path)
            logger.info(f"[AUDIO] Duración detectada (ffprobe): {duration/60:.1f} min")

            if duration > max_duration:
                os.remove(final_path)
                raise ValueError(
                    f"❌ El audio dura {duration/60:.1f} min, supera el límite de {max_duration/60} min."
                )

        except Exception as e:
            logger.error(f"[AUDIO] No se pudo determinar la duración: {e}")
            if os.path.exists(final_path):
                os.remove(final_path)
            raise

    logger.info(f"[AUDIO] Descarga completada: {final_path}")
    return final_path


# ============================
#   EJECUCIÓN DIRECTA
# ============================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python audio_downloader.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        path = download_audio(url)
        print(f"\n✅ Audio descargado en: {path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
