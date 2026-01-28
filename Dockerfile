# ============================================================
#   BASE: JetPack 6.x + CUDA 12.6 + PyTorch 2.4.0 (NVIDIA)
# ============================================================
FROM dustynv/l4t-ml:r36.4.0

ENV DEBIAN_FRONTEND=noninteractive

# ============================================================
#   SISTEMA: ffmpeg, git, wget, yt-dlp, dependencias nativas
# ============================================================
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    curl \
    python3-pip \
    python3-dev \
    libsndfile1 \
    # Dependencias necesarias para PyAV
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
#   INSTALAR yt-dlp (binario oficial compatible con Jetson)
# ============================================================
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
        -o /usr/local/bin/yt-dlp \
    && chmod +x /usr/local/bin/yt-dlp

# ============================================================
#   DIRECTORIO DE TRABAJO
# ============================================================
WORKDIR /app

# ============================================================
#   COPIAR SOLO requirements.txt (para cache)
# ============================================================
COPY wheels/ /app/wheels/
COPY requirements.txt /app/requirements.txt

# ============================================================
#   INSTALAR DEPENDENCIAS DEL PROYECTO
# ============================================================
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps -r requirements.txt

# Sobrescribir typing_extensions del sistema (necesario para Pydantic)
RUN pip install --no-cache-dir --index-url https://pypi.org/simple \
    --upgrade --force-reinstall typing_extensions==4.12.2

# Dependencias mínimas necesarias para FastAPI 0.110 + Pydantic 2.6 + Uvicorn 0.29
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps fastapi==0.110.0
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps starlette==0.37.2
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps uvicorn==0.29.0
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps click==8.1.8
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps h11==0.14.0

RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps pydantic==2.6.4
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps pydantic-core==2.16.3
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps pydantic-settings==2.2.1
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps pydantic-extra-types==2.2.0

RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps annotated-types==0.6.0
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps typing-inspection==0.3.0

RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps python-dotenv==1.1.1 
RUN pip install --no-cache-dir --index-url https://pypi.org/simple --no-deps aiosmtplib==1.1.6

# ============================================================
#   INSTALAR PyAV + faster-whisper
# ============================================================
RUN pip install --no-cache-dir av==10.0.0
RUN pip install --no-cache-dir faster-whisper==1.2.1

# ============================================================
#   COPIAR EL RESTO DEL PROYECTO
# ============================================================
COPY . /app

EXPOSE 8000

# ============================================================
#   CONFIGURACIÓN CUDA PARA JETSON
# ============================================================
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ============================================================
#   COMANDO POR DEFECTO
# ============================================================
CMD ["uvicorn", "transcriber_app.web.web_app:app", "--host", "0.0.0.0", "--port", "8000"]
