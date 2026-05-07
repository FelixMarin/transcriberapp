# transcriber_app/modules/ffmpeg_client.py

import os
import requests
import logging
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger("transcribeapp")
FFMPEG_API = os.getenv("FFMPEG_API_URL", "http://ffmpeg-api:8080")


def check_ffmpeg_api_health() -> Tuple[bool, Optional[str]]:
    """
    Verifica si FFmpeg API está operativo.
    Retorna (is_healthy, error_message)
    """
    try:
        logger.info(f"[FFMPEG] Verificando salud de FFmpeg API: {FFMPEG_API}/health")
        response = requests.get(f"{FFMPEG_API}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[FFMPEG] FFmpeg API saludable: {data}")
            return True, None
        else:
            error_msg = f"FFmpeg API respondió con status {response.status_code}"
            logger.error(f"[FFMPEG] {error_msg}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = f"FFmpeg API timeout después de 5 segundos en {FFMPEG_API}"
        logger.error(f"[FFMPEG] {error_msg}")
        return False, error_msg
        
    except requests.exceptions.ConnectionError:
        error_msg = f"No se pudo conectar a FFmpeg API en {FFMPEG_API}"
        logger.error(f"[FFMPEG] {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error verificando FFmpeg API: {str(e)}"
        logger.error(f"[FFMPEG] {error_msg}")
        return False, error_msg


def check_gpu_status() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verifica el estado de la GPU en FFmpeg API.
    Retorna (is_available, gpu_info)
    """
    try:
        logger.info(f"[FFMPEG] Verificando estado GPU: {FFMPEG_API}/gpu-status")
        response = requests.get(f"{FFMPEG_API}/gpu-status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("gpu_available"):
                logger.info(f"[FFMPEG] GPU disponible: {data.get('gpu_name')}")
                return True, data
            else:
                logger.warning("[FFMPEG] GPU no disponible, se usará CPU")
                return False, data
        else:
            logger.warning(f"[FFMPEG] No se pudo obtener estado GPU: {response.status_code}")
            return False, None
            
    except Exception as e:
        logger.warning(f"[FFMPEG] Error verificando GPU: {e}")
        return False, None


def get_audio_info(path: str) -> dict:
    """Obtiene información del audio usando ffprobe"""
    # Verificar salud antes
    is_healthy, error = check_ffmpeg_api_health()
    if not is_healthy:
        raise ConnectionError(f"FFmpeg API no disponible: {error}")
    
    logger.info(f"[FFMPEG] Obteniendo info de audio: {path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    file_size = os.path.getsize(path)
    logger.info(f"[FFMPEG] Archivo: {path}, tamaño={file_size} bytes")
    
    try:
        with open(path, "rb") as f:
            r = requests.post(
                f"{FFMPEG_API}/audio/info",
                files={"file": f},
                timeout=30
            )
        r.raise_for_status()
        result = r.json()
        logger.info(f"[FFMPEG] Info obtenida: duración={result.get('duration')}s, codec={result.get('codec')}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"[FFMPEG] Error obteniendo info: {e}")
        raise


def convert_audio(path: str, fmt: str = "wav") -> bytes:
    """Convierte audio usando ffmpeg-api"""
    # Verificar salud antes
    is_healthy, error = check_ffmpeg_api_health()
    if not is_healthy:
        raise ConnectionError(f"FFmpeg API no disponible: {error}")
    
    logger.info(f"[FFMPEG] Convertir audio: {path} -> {fmt}")
    
    # Verificar que el archivo existe
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    file_size = os.path.getsize(path)
    logger.info(f"[FFMPEG] Archivo original: {path}, tamaño={file_size} bytes")
    
    try:
        with open(path, "rb") as f:
            r = requests.post(
                f"{FFMPEG_API}/audio/convert",
                files={"file": f},
                data={"format": fmt},
                timeout=60  # Mayor timeout para conversiones largas
            )
        r.raise_for_status()
        
        result_bytes = r.content
        logger.info(f"[FFMPEG] Conversión exitosa: tamaño salida={len(result_bytes)} bytes")
        
        if len(result_bytes) < 1000:
            logger.warning(f"[FFMPEG] ¡Archivo convertido muy pequeño! {len(result_bytes)} bytes")
            # Guardar para debug
            import tempfile
            debug_path = tempfile.mktemp(suffix=f"_debug_convert.{fmt}")
            with open(debug_path, "wb") as f:
                f.write(result_bytes)
            logger.warning(f"[FFMPEG] Debug guardado en {debug_path}")
        
        return result_bytes
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[FFMPEG] Error en conversión: {e}")
        raise


def convert_to_mp3_chunked(path: str, max_size_mb: int = 22) -> dict:
    """Convierte audio a MP3 y lo divide en chunks usando FFmpeg API.

    Diseñado para audios largos que exceden el límite de 25MB.
    El servidor espera un JSON con la ruta del audio y devuelve metadata de los chunks.
    """
    # Verificar salud antes
    is_healthy, error = check_ffmpeg_api_health()
    if not is_healthy:
        raise ConnectionError(f"FFmpeg API no disponible: {error}")

    logger.info(f"[FFMPEG] Convertir a MP3 chunked: {path} (max_size_mb={max_size_mb})")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    try:
        response = requests.post(
            f"{FFMPEG_API}/audio/convert-to-mp3-chunked",
            json={"path": path, "max_size_mb": max_size_mb},
            timeout=300
        )
        response.raise_for_status()

        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("Respuesta inválida de FFmpeg API: se esperaba un objeto JSON")

        if result.get("error"):
            raise RuntimeError(f"Error en convert-to-mp3-chunked: {result.get('error')}")

        chunks = result.get("chunks", [])
        total_chunks = result.get("total_chunks", len(chunks))
        original_mp3 = result.get("original_mp3")
        needs_chunking = result.get("needs_chunking", len(chunks) > 1)

        logger.info(
            f"[FFMPEG] MP3 chunked result: total_chunks={total_chunks}, needs_chunking={needs_chunking}, original_mp3={original_mp3}"
        )

        return {
            "chunks": chunks,
            "total_chunks": total_chunks,
            "original_mp3": original_mp3,
            "needs_chunking": needs_chunking,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"[FFMPEG] Error en convert-to-mp3-chunked: {e}")
        raise


def clean_audio(path: str) -> bytes:
    """Limpia audio usando ffmpeg-api (/audio/clean)"""
    # Verificar salud antes
    is_healthy, error = check_ffmpeg_api_health()
    if not is_healthy:
        raise ConnectionError(f"FFmpeg API no disponible: {error}")
    
    logger.info(f"[FFMPEG] Limpiando audio: {path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    file_size = os.path.getsize(path)
    logger.info(f"[FFMPEG] Archivo a limpiar: {path}, tamaño={file_size} bytes")
    
    try:
        with open(path, "rb") as f:
            r = requests.post(
                f"{FFMPEG_API}/audio/clean",
                files={"file": f},
                timeout=120  # Mayor timeout para limpieza
            )
        r.raise_for_status()
        
        result_bytes = r.content
        logger.info(f"[FFMPEG] Limpieza exitosa: tamaño salida={len(result_bytes)} bytes")
        
        if len(result_bytes) < 1000:
            logger.warning(f"[FFMPEG] ¡Archivo limpiado muy pequeño! {len(result_bytes)} bytes")
            import tempfile
            debug_path = tempfile.mktemp(suffix="_debug_clean.wav")
            with open(debug_path, "wb") as f:
                f.write(result_bytes)
            logger.warning(f"[FFMPEG] Debug guardado en {debug_path}")
        
        return result_bytes
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[FFMPEG] Error en limpieza: {e}")
        raise


def validate_audio(path: str) -> dict:
    """
    Valida un archivo de audio antes de la transcripción.
    Returns un dict con la estructura:
    {
        "valid": bool,
        "optimal": bool,
        "issues": list,
        "warnings": list,
        "recommendations": list,
        "metadata": dict,
        "suggested_conversion": dict
    }
    """
    # Verificar salud antes
    is_healthy, error = check_ffmpeg_api_health()
    if not is_healthy:
        raise ConnectionError(f"FFmpeg API no disponible: {error}")
    
    logger.info(f"[FFMPEG] Validando audio: {path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    file_size = os.path.getsize(path)
    logger.info(f"[FFMPEG] Archivo a validar: {path}, tamaño={file_size} bytes")
    
    try:
        with open(path, "rb") as f:
            r = requests.post(
                f"{FFMPEG_API}/audio/validate",
                files={"file": f},
                timeout=60
            )
        r.raise_for_status()
        
        result = r.json()
        
        if result.get("valid"):
            logger.info(f"[FFMPEG] Audio válido: duración={result['metadata'].get('duration_seconds')}s")
        else:
            logger.warning(f"[FFMPEG] Audio inválido: issues={result.get('issues')}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[FFMPEG] Error en validación: {e}")
        raise


def ensure_ffmpeg_api_ready(timeout: int = 30) -> bool:
    """
    Espera a que FFmpeg API esté listo.
    Retorna True si está listo dentro del timeout, False en caso contrario.
    """
    import time
    
    logger.info(f"[FFMPEG] Esperando a que FFmpeg API esté listo (timeout={timeout}s)...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        is_healthy, error = check_ffmpeg_api_health()
        if is_healthy:
            logger.info("[FFMPEG] FFmpeg API está listo")
            return True
        logger.info(f"[FFMPEG] FFmpeg API no listo aún, reintentando... ({error})")
        time.sleep(2)
    
    logger.error(f"[FFMPEG] FFmpeg API no está listo después de {timeout} segundos")
    return False