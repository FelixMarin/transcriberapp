# Imagen base optimizada para JetPack 6.4 sin PyTorch
FROM transcriberapp-base:latest

# Crear directorio de trabajo
WORKDIR /app

# Copiar el resto del proyecto
COPY . .

# Instalar dependencias del proyecto
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Puerto por defecto (si usas uvicorn)
EXPOSE 9000

# Comando por defecto
CMD ["uvicorn", "transcriber_app.web.web_app:app", "--host", "0.0.0.0", "--port", "9000"]
