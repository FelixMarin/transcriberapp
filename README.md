# TranscriberApp

TranscriberApp es una herramienta modular diseñada para:

- **Transcribir audios mediante Whisper** con aceleración GPU en Jetson  
- **Procesar textos directamente** con análisis avanzado  
- **Generar resúmenes inteligentes** usando Gemini  
- **Extraer tareas de reuniones** (modo refinamiento)  
- **Crear resúmenes técnicos, ejecutivos o en bullet points**  
- **Guardar resultados en formato Markdown**  
- **Ejecutar nativamente en Jetson con CUDA real**  

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
echo "GEMINI_API_KEY=TU_API_KEY" > .env
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

## 🧠 Configuración avanzada

Variables en `.env`:

```bash
GEMINI_API_KEY=...
MODEL_SIZE=base
TARGET_LANG=es
LOG_LEVEL=INFO
```

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

# 📌 Comandos útiles

Este apartado reúne los comandos más importantes para trabajar con TranscriberApp en modo nativo sobre Jetson.

---

## 🎧 Descargar audio desde YouTube

```bash
python transcriber_app/modules/audio_downloader.py "URL_DEL_VIDEO"
```

Ejemplo:

```bash
python transcriber_app/modules/audio_downloader.py "https://youtu.be/osKyvYJ3PRM?si=LM23Iu92g0oxG8ox"
```

El archivo descargado se guarda en `audios/`.

---

## 🧠 Ejecutar el pipeline completo

### Formato general

```bash
python -m transcriber_app.main [audio|texto] [nombre] [modo]
```

### Ejemplo (transcripción + resumen técnico)

```bash
python -m transcriber_app.main audio ejemplo1 tecnico
```

Esto genera:

- `transcripts/ejemplo1.txt`  
- `outputs/ejemplo1_tecnico.md`

---

## 🌐 Ejecutar la API web

```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 8000
```

Acceso:

```
http://localhost:8000
```

---

## ▶️ Ejecutar la app con el script de arranque

```bash
./start.sh
```

Asegúrate de haber dado permisos:

```bash
chmod +x start.sh
```

---

## 🔥 Matar procesos Python que se quedan colgados

Listar procesos:

```bash
ps aux | grep python
```

Matar uno:

```bash
kill -9 PID
```

---

## 🧪 Ejecutar tests

```bash
pytest -q
```

---

## 🧹 Limpiar cachés de Python

```bash
find . -type d -name "__pycache__" -exec rm -r {} +
```

---

## 🧩 Verificar CUDA y PyTorch en el host

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
- Streaming  
- Diarización  

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
