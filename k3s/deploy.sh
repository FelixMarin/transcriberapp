#!/bin/bash

set -e

# ===== INICIO DEL TEMPORIZADOR =====
START_TIME=$(date +%s)

# ===== CONFIGURACIÓN =====
IMAGE_NAME="felixmurcia/transcriberapp"
NAMESPACE="default"
DEPLOYMENT="transcriberapp"
APP_LABEL="transcriberapp"

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
echo "  🧹 Eliminando imágenes antiguas de transcriberapp"
echo "======================================"

IMAGES_TO_DELETE=$(docker images felixmurcia/transcriberapp --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" \
  | sort -k2 -r \
  | tail -n +2 \
  | awk '{print $1}')

for IMG in $IMAGES_TO_DELETE; do
  echo "🗑️  Eliminando imagen antigua: $IMG"
  docker rmi -f "$IMG" || true
done

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
echo "  🧹 Limpiando imágenes dangling y contenedores parados"
echo "======================================"

docker image prune -f
docker container prune -f

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
