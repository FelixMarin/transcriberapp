#!/bin/bash

# Construir imagen base
echo "Construyendo imagen base..."
sudo docker build -f Dockerfile.base -t transcriberapp-base .

# Construir imagen de la aplicación
echo "Construyendo imagen de la aplicación..."
sudo docker build -t transcriberapp .

# Probar con NVIDIA Container Toolkit
echo "Probando container con GPU..."
sudo docker run --rm --runtime nvidia transcriberapp-base:latest python3 -c "
import faster_whisper
print('=== Testing faster-whisper on Jetson ===')
try:
    model = faster_whisper.WhisperModel('tiny', device='cuda', compute_type='float16')
    print('✅ faster-whisper funciona con GPU')
    
    # Probar inferencia simple
    segments, info = model.transcribe('/dev/null', beam_size=5)
    print(f'✅ Modelo cargado correctamente')
    print(f'   Idioma detectado: {info.language if hasattr(info, \"language\") else \"N/A\"}')
    
except Exception as e:
    print(f'❌ Error GPU: {e}')
    import traceback
    traceback.print_exc()
    
    # Intentar CPU como fallback
    try:
        model = faster_whisper.WhisperModel('tiny', device='cpu')
        print('⚠️  Funciona solo en CPU')
    except Exception as e2:
        print(f'❌ Error CPU: {e2}')
"

# Verificar instalaciones
echo "Verificando instalaciones..."
sudo docker run --rm --runtime nvidia transcriberapp-base:latest python3 -c "
import faster_whisper
import onnxruntime
import ctranslate2

print('=== Versiones instaladas ===')
print(f'faster-whisper: {faster_whisper.__version__}')
print(f'onnxruntime: {onnxruntime.__version__}')
print(f'ctranslate2: {ctranslate2.__version__}')

# Verificar GPU
print('\\n=== Verificación GPU ===')
print(f'ONNX Runtime devices: {onnxruntime.get_available_providers()}')
print(f'CTranslate2 disponible: {ctranslate2.get_cuda_device_count() > 0}')
"