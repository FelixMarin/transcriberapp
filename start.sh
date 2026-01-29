#!/bin/bash

# ============================================
#  TranscriberApp - Script de arranque
#  Ejecuta la aplicación con el entorno virtual
# ============================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv_transcriber"
MAIN_APP="transcriber_app.web.web_app:app"
PYTHON_BIN="$VENV_DIR/bin/python"

echo "📌 Directorio del proyecto: $APP_DIR"
echo "📌 Activando entorno virtual..."

# Verificar que el entorno virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ ERROR: No se encontró el entorno virtual en:"
    echo "   $VENV_DIR"
    echo "   Crea el entorno con:"
    echo "   python3 -m venv venv_transcriber"
    exit 1
fi

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

echo "🚀 Iniciando TranscriberApp..."
echo "🌐 Servidor disponible en: http://127.0.0.1:9000"

# Ejecutar FastAPI con Uvicorn usando el mismo comando que funciona
exec "$PYTHON_BIN" -m uvicorn "$MAIN_APP" \
  --host 0.0.0.0 \
  --port 9000 \
  --log-level debug

