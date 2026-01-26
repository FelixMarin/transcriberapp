# TranscriberApp

TranscriberApp es una herramienta modular diseñada para:

- Transcribir audios mediante Whisper
- Procesar textos directamente
- Generar resúmenes avanzados usando Gemini (Google Generative AI)
- Extraer tareas de reuniones (modo refinamiento)
- Crear resúmenes técnicos, ejecutivos o en bullet points
- Guardar resultados en formato Markdown

---

## 🚀 Características principales

- **Transcripción automática** de archivos `.mp3`
- **Procesamiento directo** de archivos `.txt`
- **Modos de análisis**: técnico, refinamiento, ejecutivo, bullet, default
- **Salida estructurada** en `outputs/`
- **Transcripciones guardadas** en `transcripts/`
- **Arquitectura modular y extensible**

---

## 📦 Librerías utilizadas

### Dependencias principales

- `google-generativeai` — Cliente oficial para modelos Gemini
- `whisper` — Motor de transcripción de audio
- `python-dotenv` — Carga de variables de entorno
- `ffmpeg` — Requerido por Whisper para procesar audio
- `tqdm` — Barras de progreso
- `numpy` — Dependencia interna de Whisper

### Dependencias del sistema

Asegúrate de tener instalado:

```bash
sudo apt install ffmpeg
```

TranscriberApp/
│
├── audios/                     # Archivos .mp3 de entrada
├── transcripts/                # Transcripciones generadas (.txt)
├── outputs/                    # Resultados finales (.md)
│
├── transcriber_app/
│   ├── main.py                 # Punto de entrada principal
│   ├── modules/
│   │   ├── audio_receiver.py   # Carga de audio
│   │   ├── audio_downloader.py # Descarga de audio desde URL
│   │   ├── transcriber.py      # Whisper
│   │   ├── gemini_client.py    # Cliente Gemini
│   │   ├── summarizer.py       # Lógica de resumen
│   │   ├── output_formatter.py # Guardado de resultados
│   │   ├── prompt_factory.py   # Prompts por modo
│   │
│   ├── runner/
│       ├── orchestrator.py     # Orquestación del pipeline
│
├── venv/                       # Entorno virtual
├── README.md
└── .env                        # API key de Gemini

### Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Instalar dependencias:
```bash
pip install -r requirements.txt
```

### Crear archivo .env:
```bash
GEMINI_API_KEY=TU_API_KEY_AQUI
```

## Modos disponibles
```bash
Modo	        Descripción
default	        Resumen simple
tecnico	        Resumen técnico avanzado
refinamiento	Extrae tareas, subtareas, decisiones y backlog
ejecutivo	    Resumen ejecutivo de 5–8 líneas
bullet	        Resumen en bullets
```

# Ejecución

## 1. Descargar audio desde una URL
```bash
python transcriber_app/modules/audio_downloader.py "https://www.youtube.com/watch?v=XXXX"
```

## 2. Procesar un archivo de audio
```bash
python -m transcriber_app.main audio nombre_archivo modo
```
## Ejemplo: 
```bash
python -m transcriber_app.main audio reunion1 tecnico
```
Esto:
- Carga audios/reunion1.mp3

- Transcribe con Whisper

- Genera un resumen técnico

- Guarda:  
-   transcripts/reunion1.txt  
-   outputs/reunion1_tecnico.md

## 3. Procesar un archivo de texto
```bash
python -m transcriber_app.main texto nombre_archivo modo
```
## Ejemplo: 
```bash
python -m transcriber_app.main texto sprint_refinement refinamiento
```
Esto:

- Carga transcripts/sprint_refinement.txt
- Genera backlog completo del refinamiento
- Guarda:
-- outputs/sprint_refinement_refinamiento.md

## Notas importantes
- No incluyas extensiones al ejecutar comandos (.mp3 o .txt se añaden automáticamente).
- Los resultados siempre se guardan en outputs/.
- Las transcripciones de audio se guardan en transcripts/.

## Futuras mejoras
- Exportación a JSON/YAML para Jira/Linear
- Modo "acta de reunión"
- Modo "resumen para email"
- Interfaz web ligera

## Autor
Proyecto desarrollado por Félix, optimizado para flujos reales de trabajo en entornos técnicos y productivos.

