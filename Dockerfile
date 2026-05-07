FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Madrid

WORKDIR /app

# Copiamos el código
COPY . .

# Limpiar pycache
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} +

# Instalamos dependencias Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Instalamos el paquete en modo editable
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/logs && \
    chmod -R 777 /app/logs && \ 
    mkdir -p /app/data && \
    chmod -R 777 /app/data && \
    mkdir -p /app/config && \
    chmod -R 777 /app/config && \
    mkdir -p /app/audios && \
    chmod -R 777 /app/audios && \
    mkdir -p /app/outputs && \
    chmod -R 777 /app/outputs && \
    mkdir -p /app/audios/audios_chunks && \
    chmod -R 777 /app/audios/audios_chunks && \
    mkdir -p /app/transcripts && \
    chmod -R 777 /app/transcripts && \
    mkdir -p /app/outputs && \
    chmod -R 777 /app/outputs && \
    mkdir -p /app/outputs/metrics && \
    chmod -R 777 /app/outputs/metrics && \
    mkdir -p /app/recordings && \
    chmod -R 777 /app/recordings

EXPOSE 9000
