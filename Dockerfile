# Imagen base optimizada para JetPack 6.4 sin PyTorch
FROM transcriberapp-base:latest

# Crear directorio de trabajo
WORKDIR /app

# Copiar el resto del proyecto
COPY . .

# Instalar dependencias del proyecto
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Variables de entorno para Jetson
ENV CUDA_VISIBLE_DEVICES=0
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}
ENV TF_FORCE_GPU_ALLOW_GROWTH=true

# Puerto por defecto (si usas uvicorn)
EXPOSE 9000

# Comando por defecto (puedes cambiarlo si quieres)
CMD ["uvicorn", "transcriber_app.web.web_app:app", "--host", "0.0.0.0", "--port", "9000"]
