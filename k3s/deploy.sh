#!/bin/bash

set -e

# ===== INICIO DEL TEMPORIZADOR =====
START_TIME=$(date +%s)

# ===== CONFIGURACIÓN =====
IMAGE_NAME="felixmurcia/transcriberapp"
NAMESPACE="default"           # Namespace donde está desplegada la app
DEPLOYMENT="transcriberapp"   # Nombre del deployment en Kubernetes
APP_LABEL="transcriberapp"    # Label 'app' usado en tus pods

# ===== GENERAR TAG AUTOMÁTICO =====
TAG=$(date +"v%Y%m%d-%H%M")
FULL_IMAGE="$IMAGE_NAME:$TAG"

echo "======================================"
echo "  🚀 Construyendo imagen: $FULL_IMAGE"
echo "======================================"

docker build -t $FULL_IMAGE .

echo "======================================"
echo "  📤 Subiendo imagen al registro"
echo "======================================"

docker push $FULL_IMAGE

echo "======================================"
echo "  📝 Actualizando Deployment en Kubernetes"
echo "======================================"

kubectl set image deployment/$DEPLOYMENT \
  $DEPLOYMENT=$FULL_IMAGE \
  -n $NAMESPACE

echo "======================================"
echo "  🔄 Forzando rollout del despliegue"
echo "======================================"

kubectl rollout restart deployment/$DEPLOYMENT -n $NAMESPACE

echo "======================================"
echo "  ⏳ Esperando a que el nuevo pod esté listo..."
echo "======================================"

kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE

echo "======================================"
echo "  🧹 Limpiando imágenes antiguas de Docker"
echo "======================================"

docker image prune -f --filter "until=24h"

# ===== FIN DEL TEMPORIZADOR =====
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

MINUTES=$((TOTAL_TIME / 60))
SECONDS=$((TOTAL_TIME % 60))

echo "======================================"
echo "  ⏱️  Tiempo total del despliegue: ${MINUTES}m ${SECONDS}s"
echo "======================================"

echo "======================================"
echo "  📜 Mostrando logs del nuevo pod (Ctrl+C para salir)"
echo "======================================"

kubectl logs -n $NAMESPACE -l app=$APP_LABEL -f
