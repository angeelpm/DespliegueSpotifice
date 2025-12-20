#!/bin/bash
# Script para ejecutar MediaRender local conectado a Docker IceGrid

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=== Iniciando MediaRender Local ==="
echo "Conectando a IceGrid en localhost:4061"
echo ""

# Configuración inline para el MediaRender local
cat > /tmp/mediarender-local.config <<EOF
Ice.Default.Locator=SpotificeGrid/Locator:tcp -h localhost -p 4061
MediaRenderAdapter.Endpoints=tcp -h 0.0.0.0 -p 10000
Ice.Override.ConnectTimeout=5000
EOF

echo "MediaRender disponible en localhost:10000"
echo "Identidad: mediaRender"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

python3 media_render.py /tmp/mediarender-local.config
