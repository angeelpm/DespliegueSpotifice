#!/bin/bash

BASE_DIR="/home/angel/Escritorio/SpoificeDespliegue/DespliegueSpotifice/spotifice-icegrid-deploy"

echo "=============================================="
echo " Deteniendo Spotifice IceGrid"
echo "=============================================="
echo ""

echo "Deteniendo procesos..."

# Matar procesos de IceGrid
pkill -9 -f icegridregistry 2>/dev/null && echo "  ✓ Registry detenido"
pkill -9 -f icegridnode 2>/dev/null && echo "  ✓ Nodos detenidos"
pkill -9 -f icepatch2server 2>/dev/null && echo "  ✓ IcePatch2 detenido"

# Limpiar archivos PID
rm -f "$BASE_DIR/.registry.pid" "$BASE_DIR/.node1.pid" "$BASE_DIR/.node2.pid" 2>/dev/null

echo ""
echo "=============================================="
echo " ✓ Sistema detenido correctamente"
echo "=============================================="
