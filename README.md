# TranscriberApp

[![CI](https://github.com/FelixMarin/transcriberapp/actions/workflows/ci.yml/badge.svg)](https://github.com/FelixMarin/transcriberapp/actions/workflows/ci.yml) [![Coverage](https://img.shields.io/badge/coverage-N%2FA-lightgrey.svg)](https://github.com/FelixMarin/transcriberapp)

TranscriberApp es una herramienta modular diseñada para:

- **Transcribir audios mediante Whisper** con aceleración GPU en Jetson  
- **Procesar textos directamente** con análisis avanzado  
- **Generar resúmenes inteligentes** usando Gemini  
- **Extraer tareas de reuniones** (modo refinamiento)  
- **Crear resúmenes técnicos, ejecutivos o en bullet points**  
- **Guardar resultados en formato Markdown**  
- **Ejecutar nativamente en Jetson con CUDA real**  
- **Interactuar con un asistente IA integrado**  
- **Consultar y ampliar información mediante chat con streaming de tokens**  
- **Imprimir el resultado procesado en PDF**  
- **Interfaz moderna con overlay de carga y bloqueo de interacción**  

![Imagen de muestra](https://raw.githubusercontent.com/FelixMarin/transcriberapp/refs/heads/main/screen.jpg)

---

## 🚀 Características principales

- **Transcripción automática** de archivos `.mp3` con Whisper acelerado por GPU  
- **Procesamiento directo** de archivos `.txt`  
- **Modos de análisis**: técnico, refinamiento, ejecutivo, bullet, default  
- **Salida estructurada** en `outputs/`  
- **Transcripciones guardadas** en `transcripts/`  
- **Arquitectura modular y extensible**  
- **Compatibilidad total con NVIDIA Jetson**  
- **Wheels personalizados para PyTorch CUDA en JetPack 6.x**  
- **Ejecución nativa optimizada para JetPack R36.x**  
- **Chat IA integrado con historial y contexto**  
- **Streaming de tokens para respuestas en tiempo real**  
- **Overlay de bloqueo con spinner durante el procesamiento**  
- **Botón de impresión PDF en el panel de resultados**  
- **Control inteligente del botón "Procesar y enviar"**  
  - Solo se habilita cuando hay audio, nombre, email, modo y no existen resultados previos  

---

## 🖥️ Compatibilidad

### **Entornos soportados:**
- ✅ **NVIDIA Jetson** (Orin Nano, Xavier, AGX Orin)  
- ✅ **JetPack 6.x (R36.x)**  
- ✅ **Python 3.10**  
- ✅ **CUDA 12.4 en el host**  

### ⚠️ Nota importante sobre JetPack R36.4.7

TranscriberApp funciona perfectamente en ejecución nativa.  
No se recomienda el uso de contenedores en esta versión de JetPack debido a incompatibilidades con CUDA.

---

## 📦 Stack tecnológico

### **Backend:**
- **Whisper** (OpenAI)  
- **PyTorch 2.3.0 + CUDA 12.4** (wheels personalizados para Jetson)  
- **FastAPI**  
- **Google Gemini API**  
- **ONNX Runtime GPU**  

### **Frontend:**
- HTML/CSS/JS  
- Chat IA con streaming  
- Overlay de carga  
- Botón de impresión PDF  
- Renderizado Markdown con `marked.js`  

### **Infraestructura:**
- **Ejecución nativa en Jetson**  
- **Entorno virtual Python 3.10**  

---

## 🏗️ Arquitectura del proyecto

```
TranscriberApp/
│
├── audios/                     
├── transcripts/                
├── outputs/                    
├── wheels/                     
│   ├── torch_cuda_jetpack-2.3.0-py3-none-any.whl
│   ├── torchaudio-2.3.0+952ea74-cp310-cp310-linux_aarch64.whl
│   ├── torchvision-0.18.0a0+6043bc2-cp310-cp310-linux_aarch64.whl
│   ├── openai_whisper-20250625-py3-none-any.whl
│   └── onnxruntime_gpu-1.19.0-cp310-cp310-linux_aarch64.whl
│
├── transcriber_app/
│   ├── main.py
│   ├── modules/
│   ├── runner/
│   └── web/
│       ├── static/
│       │   ├── js/
│       │   │   ├── recorder.js
│       │   │   ├── chat.js
│       │   │   ├── streaming.js
│       │   │   ├── overlay.js
│       │   │   └── ui_validations.js
│       │   ├── css/
│       │   └── img/
│       └── templates/
│
├── requirements_clean.txt      
├── requirements.txt            
├── .env                        
└── README.md
```

---

## ⚙️ Instalación (Ejecución nativa recomendada)

```bash
git clone <repositorio>
cd TranscriberApp

python3 -m venv venv_transcriber
source venv_transcriber/bin/activate

pip install -r requirements_clean.txt

pip install wheels/torch_cuda_jetpack-2.3.0-py3-none-any.whl
pip install wheels/torchaudio-2.3.0+952ea74-cp310-cp310-linux_aarch64.whl
pip install wheels/torchvision-0.18.0a0+6043bc2-cp310-cp310-linux_aarch64.whl
pip install wheels/openai_whisper-20250625-py3-none-any.whl
pip install wheels/onnxruntime_gpu-1.19.0-cp310-cp310-linux_aarch64.whl
```

Configurar API Key:

```bash
echo "GOOGLE_API_KEY=TU_API_KEY" > .env
```

---

## 🎯 Modos disponibles

| Modo | Descripción |
|------|-------------|
| `default` | Resumen general |
| `tecnico` | Resumen técnico |
| `refinamiento` | Tareas, backlog, decisiones |
| `ejecutivo` | Resumen corto para dirección |
| `bullet` | Puntos clave |

---

## 🚀 Ejecución

### CLI

```bash
python -m transcriber_app.main audio ejemplo tecnico
```

### Web API

```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 8000
```

Acceder a:

```
http://localhost:8000
```

---

## 📁 Estructura de salida

```
transcripts/
outputs/
```

---

## 🧠 Funcionalidades avanzadas del frontend

### ✔ Chat IA integrado
- Conversación contextual basada en la transcripción y el resumen  
- Historial persistente durante la sesión  
- Respuestas en tiempo real mediante **streaming de tokens**  
- Formato enriquecido con saltos de línea y listas  

### ✔ Overlay de carga
- Bloquea la interfaz durante el procesamiento  
- Spinner centrado  
- Evita interacciones erróneas  

### ✔ Botón de impresión PDF
- Disponible en el panel de **Resultado Procesado**  
- Imprime únicamente el contenido del resumen  
- Formato limpio y preparado para documentación  

### ✔ Validación inteligente del botón "Procesar y enviar"
El botón solo se habilita cuando:

- Hay un audio grabado  
- Nombre, email y modo están completos  
- No existe transcripción previa  
- No existe resultado procesado  

---

## 🧠 Configuración avanzada

Variables en `.env`:

```bash
GOOGLE_API_KEY=...
SMTP_HOST=...
SMTP_PORT=465
SMTP_USER=...
SMTP_PASS=...
USE_MODEL=gemini-2.5-flash-lite
LANGUAGE=es
```

---

## 🌐 Acceso desde la red local (IMPORTANTE)

Para acceder a la interfaz web de **TranscriberApp** desde cualquier PC, móvil o tablet dentro de la misma red local, es necesario usar **HTTPS**, ya que los navegadores bloquean el acceso al micrófono (`getUserMedia()`) en conexiones HTTP que no sean `localhost`.

### ✔ Requisitos

1. **Caddy** instalado como reverse proxy HTTPS  
2. **Uvicorn** ejecutándose en el Jetson en `127.0.0.1:9000`  
3. **Caddy** escuchando en el puerto **443** y redirigiendo a Uvicorn  

### ✔ Configuración de Caddy

Archivo: `/etc/caddy/Caddyfile`

```
<IP_DEL_JETSON> {
    reverse_proxy 127.0.0.1:9000
}
```

Ejemplo:

```
192.168.0.105 {
    reverse_proxy 127.0.0.1:9000
}
```

Reiniciar Caddy:

```
sudo systemctl restart caddy
```

### ✔ Arranque de la aplicación

El servidor FastAPI debe ejecutarse **solo en local**, sin HTTPS:

```
uvicorn transcriber_app.web.web_app:app \
    --host 127.0.0.1 \
    --port 9000
```

### ✔ Acceso desde otros dispositivos

En cualquier navegador dentro de la red:

```
https://<IP_DEL_JETSON>
```

Ejemplo:

```
https://192.168.0.105
```

⚠ **No usar `:9000`**, ya que ese puerto no sirve HTTPS.

### ✔ ¿Por qué es necesario?

Los navegadores solo permiten usar el micrófono si la página se sirve desde:

- `https://…`
- `http://localhost`
- `http://127.0.0.1`

Por eso, para acceder desde otro PC o móvil, es obligatorio usar **HTTPS**.

---

## 🐛 Solución de problemas

### PyTorch sin CUDA
Instalar wheels personalizados.

### Whisper lento
Usar modelo más pequeño:

```bash
export MODEL_SIZE=tiny
```

### ONNX GPU no carga
Verificar:

```bash
python -c "import onnxruntime as ort; print(ort.get_device())"
```

---

## 📌 Comandos útiles

### 🎧 Descargar audio desde YouTube

```bash
python transcriber_app/modules/audio_downloader.py "URL_DEL_VIDEO"
```

Ejemplo:

```bash
python transcriber_app/modules/audio_downloader.py "https://youtu.be/osKyvYJ3PRM?si=LM23Iu92g0oxG8ox"
```

### 🧠 Ejecutar el pipeline completo

```bash
python -m transcriber_app.main [audio|texto] [nombre] [modo]
```

Ejemplo:

```bash
python -m transcriber_app.main audio ejemplo1 tecnico
```

### 🌐 Ejecutar la API web

```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 8000
```

### ▶️ Ejecutar la app con el script de arranque

```bash
./start.sh
chmod +x start.sh
```

### 🔥 Matar procesos Python colgados

```bash
ps aux | grep python
kill -9 PID
```

### 🧪 Ejecutar tests

```bash
pytest -q
```

### 🧹 Limpiar cachés de Python

```bash
find . -type d -name "__pycache__" -exec rm -r {} +
```

### 🧩 Verificar CUDA y PyTorch

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📊 Rendimiento en Jetson Orin Nano

| Componente | Tiempo | GPU |
|------------|--------|-----|
| Whisper base | 2–3 min | ~2GB |
| Gemini | 5–10 s | <1GB |

---

## 🔄 Flujo típico

1. Subir audio  
2. Transcribir  
3. Resumir  
4. Exportar  

---

## 📈 Roadmap

- Exportación a Jira  
- Dashboard web  
- Diarización  
- Exportación avanzada a PDF  
- Modo conversación larga  

---

## 🛡️ Seguridad

- API keys en `.env`  
- Datos locales  

---

## 📄 Licencia

MIT

---

## ✨ Agradecimientos

OpenAI, Google, NVIDIA, FastAPI, comunidad Jetson.
