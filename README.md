# **TranscriberApp**

TranscriberApp es una aplicación web moderna para transcribir audios, generar resúmenes inteligentes y conversar con un asistente IA contextual.  
Toda la inteligencia se ejecuta mediante **APIs externas**:

- **Groq Whisper** para transcripción  
- **Gemini** para resumen, análisis y chat  

La aplicación está diseñada para ejecutarse de forma estable en **Kubernetes**, con almacenamiento persistente y acceso seguro mediante **Tailscale + HTTPS**.

![Imagen de muestra](https://raw.githubusercontent.com/FelixMarin/transcriberapp/refs/heads/main/screen1.jpg)

---

## 🚀 Características principales

- Transcripción de audio vía **Groq Whisper API**  
- Resumen y análisis con **Gemini**  
- Chat IA con streaming de tokens  
- Interfaz web ligera (HTML/JS)  
- Resultados persistentes en PVCs  
- HTTPS automático con certificados de Tailscale  
- API REST con FastAPI  
- Arquitectura modular y extensible  

---

## 🖥️ Compatibilidad

- Linux  
- macOS  
- Windows  
- Kubernetes (k3s, k8s estándar, MicroK8s, etc.)  
- Python 3.10  

> No requiere GPU, CUDA ni dependencias de hardware específicas.

---

## 📦 Stack tecnológico

### Backend
- FastAPI  
- Groq Whisper API  
- Gemini (Google Generative AI)  
- Requests / HTTPX  
- FastAPI-Mail  

### Frontend
- HTML / CSS / JavaScript  
- Streaming SSE  
- Renderizado Markdown  
- Overlay de carga  
- Impresión PDF  

### Infraestructura
- Kubernetes  
- PVCs para audios, transcripts y outputs  
- Tailscale para HTTPS  
- NodePort para exposición del servicio  

---

## 🏗️ Estructura del proyecto (carpetas principales)

```
TranscriberApp/
├── audios/
├── transcripts/
├── outputs/
├── k3s/
├── transcriber_app/
│   ├── modules/
│   ├── web/
│   ├── runner/
│   └── main.py
├── requirements.txt
├── README.md
└── .env
```

---

## ⚙️ Instalación (desarrollo local)

```bash
git clone <repositorio>
cd TranscriberApp

python3 -m venv venv_transcriber
source venv_transcriber/bin/activate

pip install -r requirements.txt
```

Configurar API Keys:

```bash
echo "GROQ_API_KEY=tu_clave" >> .env
echo "GOOGLE_API_KEY=tu_clave" >> .env
```

---

## 🎯 Modos disponibles

| Modo | Descripción |
|------|-------------|
| `default` | Resumen general |
| `tecnico` | Resumen técnico |
| `refinamiento` | Tareas, backlog, decisiones |
| `ejecutivo` | Resumen corto |
| `bullet` | Puntos clave |

---

## 🚀 Ejecución local

### CLI

```bash
python -m transcriber_app.main audio ejemplo tecnico
```

### Web API

```bash
uvicorn transcriber_app.web.web_app:app --host 0.0.0.0 --port 9000
```

Acceso:

```
http://localhost:9000
```

---

# ☸️ Despliegue en Kubernetes

TranscriberApp está diseñada para ejecutarse de forma estable en Kubernetes.

### Componentes incluidos:

- **Deployment**  
- **Service NodePort**  
- **PVCs**  
- **Secrets**  
- **Certificados Tailscale** montados desde el host  

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: transcriberapp-secrets
type: Opaque
stringData:
  groq_api_key: "GSK_XXXX"
  google_api_key: "AIzaXXXX"
```

### Certificados Tailscale

Montados desde:

```
/var/lib/tailscale/certs
```

### Acceso final

```
https://ubuntu.tailXXXX.ts.net:30090/
```

---

# 🔐 HTTPS con Tailscale

### Generar certificado

```
sudo tailscale cert ubuntu.tailXXXX.ts.net
```

Esto crea:

```
/var/lib/tailscale/certs/ubuntu.tailXXXX.ts.net.crt
/var/lib/tailscale/certs/ubuntu.tailXXXX.ts.net.key
```

El Deployment monta estos archivos en `/certs`.

---

# 📁 Estructura de salida

```
transcripts/
outputs/
```

---

# 🧪 Tests unitarios y de integración

TranscriberApp incluye una batería completa de tests:

- Tests unitarios de módulos internos  
- Tests de integración del pipeline  
- Tests del frontend (JS)  
- Tests del backend (FastAPI)  

### Ejecutar tests

```bash
pytest -q
```

### Ejecutar tests con cobertura

```bash
pytest --cov=transcriber_app
```

---

# 🧠 Configuración avanzada

Variables en `.env`:

```bash
GROQ_API_KEY=...
GOOGLE_API_KEY=...
SMTP_HOST=...
SMTP_PORT=465
SMTP_USER=...
SMTP_PASS=...
USE_MODEL=gemini-2.5-flash-lite
LANGUAGE=es
```

---

# 📌 Comandos útiles

Descargar audio desde YouTube:

```bash
python transcriber_app/modules/audio_downloader.py "URL"
```

Ejecutar pipeline completo:

```bash
python -m transcriber_app.main audio ejemplo tecnico
```

Ver logs en Kubernetes:

```bash
kubectl logs -l app=transcriberapp -f
```

Reiniciar la app:

```bash
kubectl delete pod -l app=transcriberapp
```

# TranscriberApp — Despliegue + Kubernetes (k3s) + Tailscale + HTTPS

Este documento describe **todo el proceso real** seguido para desplegar TranscriberApp en un usando:

- Docker optimizado para Jetson (L4T)
- Kubernetes k3s
- Tailscale para acceso remoto seguro
- HTTPS automático con certificados de Tailscale
- NodePort para exposición del servicio
- Persistencia con PVCs

Incluye además una sección completa de **troubleshooting**, basada en los problemas reales encontrados durante la instalación.

---

# 1. 🧱 Estructura del proyecto

```
TranscriberApp/
├── transcriber_app/
├── utils/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress/ (no usado)
│   └── storage/
├── audios/ (PVC)
├── transcripts/ (PVC)
├── outputs/ (PVC)
└── .dockerignore
```

---

# 2. 🐳 Construcción de la imagen Docker optimizada

## 2.1 Problema inicial
Las primeras imágenes pesaban **16.2 GB**, lo que hacía imposible:

- subirlas a Docker Hub  
- que containerd las extrajera  
- que k3s las ejecutara  

## 2.2 Solución
Se creó un Dockerfile optimizado basado en:

```
FROM nvcr.io/nvidia/l4t-base:r36.3.0
```

Este contenedor es:

- compatible con JetPack 6.x  
- mucho más ligero que `l4t-jetpack`  
- suficiente para Python + FFmpeg  

## 2.3 `.dockerignore` crítico
Para evitar copiar basura dentro de la imagen:

```
venv/
audios/
outputs/
transcripts/
wheels/
__pycache__/
*.pyc
k8s/secret.yaml
```

Esto redujo la imagen final a **~2 GB**.

---

# 3. 🚀 Despliegue en Kubernetes (k3s)

## 3.1 Deployment con HTTPS
El contenedor se arranca con Uvicorn en modo SSL:

```yaml
command:
  - uvicorn
  - transcriber_app.web.web_app:app
  - --host
  - "0.0.0.0"
  - --port
  - "9000"
  - --ssl-keyfile
  - /certs/ubuntu.tailXXXXXX.ts.net.key
  - --ssl-certfile
  - /certs/ubuntu.tailXXXXXX.ts.net.crt
```

Los certificados se montan desde el host:

```yaml
volumeMounts:
  - name: tailscale-certs
    mountPath: /certs
    readOnly: true

volumes:
  - name: tailscale-certs
    hostPath:
      path: /var/lib/tailscale/certs
      type: Directory
```

## 3.2 Service expuesto como NodePort
Para acceso desde Tailscale:

```yaml
type: NodePort
ports:
  - port: 9000
    targetPort: 9000
    nodePort: 30090
```

Acceso final:

```
https://ubuntu.tailXXXXXX.ts.net:30090/
```

---

# 4. 🔐 HTTPS con Tailscale

## 4.1 Generación del certificado
Tailscale solo permite certificados para **dominios válidos del tailnet**.

Comando correcto:

```
sudo tailscale cert ubuntu.tailXXXXXX.ts.net
```

Esto genera:

```
/var/lib/tailscale/certs/ubuntu.tailXXXXXX.ts.net.crt
/var/lib/tailscale/certs/ubuntu.tailXXXXXX.ts.net.key
```

## 4.2 Renovación automática
Tailscale renueva los certificados sin intervención manual.

---

# 5. 🛠️ Troubleshooting completo

Esta sección recoge **todos los problemas reales** encontrados y cómo se resolvieron.

---

## ❌ Problema 1 — La imagen Docker pesaba 16 GB
**Causa:**  
`COPY . .` copiaba:

- venv  
- audios  
- outputs  
- wheels  
- docs  
- cachés  

**Solución:**  
Crear `.dockerignore` y usar `l4t-base`.

---

## ❌ Problema 2 — containerd no podía extraer la imagen
**Causa:**  
Imagen demasiado grande para Jetson.

**Solución:**  
Reducir la imagen a ~2 GB.

---

## ❌ Problema 3 — `nvcr.io/nvidia/l4t-base:r36.4.0` no existe
**Causa:**  
Esa etiqueta no está publicada en NGC.

**Solución:**  
Usar:

```
nvcr.io/nvidia/l4t-base:r36.3.0
```

---

## ❌ Problema 4 — Error al descargar imágenes de NGC
**Causa:**  
NGC requiere autenticación.

**Solución:**

```
docker login nvcr.io
username: $oauthtoken
password: <API key de NGC>
```

---

## ❌ Problema 5 — El pod no era accesible desde Tailscale
**Causa:**  
El Service era `ClusterIP`.

**Solución:**  
Cambiar a `NodePort`.

---

## ❌ Problema 6 — HTTPS no funcionaba
**Causa:**  
Intento de generar certificado para un dominio inválido:

```
tailscale cert transcriberapp → invalid domain
```

**Solución:**  
Usar el dominio real del tailnet:

```
tailscale cert ubuntu.tailXXXXXX.ts.net
```

---

## ❌ Problema 7 — Traefik `svclb-traefik` en CrashLoopBackOff
**Causa:**  
k3s crea un LoadBalancer interno que falla si:

- no hay MetalLB  
- Tailscale interfiere  
- puertos 80/443 están ocupados  

**Solución:**  
Ignorar Traefik y usar NodePort + Tailscale HTTPS.

---

## ❌ Problema 8 — El Jetson tenía imágenes antiguas ocupando 45 GB
**Solución:**

```
docker rmi transcriberapp-base:latest
docker rmi transcriberapp-container:latest
docker system prune -a
```

---

# 6. ✔ Estado final del sistema

- TranscriberApp funcionando en Kubernetes  
- HTTPS real con certificados de Tailscale  
- Acceso remoto seguro desde cualquier dispositivo  
- Imagen Docker ligera y optimizada  
- PVCs funcionando  
- Traefik no necesario para este caso  
- Clúster estable  

---

# 7. 📡 Acceso final a la aplicación

```
https://ubuntu.tailXXXXXX.ts.net:30090/
```

---

# 8. 📦 Comandos útiles

Ver pods:

```
kubectl get pods -A
```

Ver logs:

```
kubectl logs -l app=transcriberapp -f
```

Reiniciar la app:

```
kubectl delete pod -l app=transcriberapp
```

---

# 9. 🧹 Limpieza de imágenes Docker

```
docker system df
docker rmi <imagen>
docker system prune -a
```

---

# 10. 📝 Notas finales

Este README documenta **todo el proceso real**, incluyendo errores, decisiones técnicas y soluciones aplicadas.  
Es una guía completa para reproducir el despliegue en cualquier Jetson con k3s + Tailscale.

```

---

# 📄 Licencia

MIT

---

## ✨ Agradecimientos

OpenAI, Google, NVIDIA, FastAPI, comunidad Jetson.
