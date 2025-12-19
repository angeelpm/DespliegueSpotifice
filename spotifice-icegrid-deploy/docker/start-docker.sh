#!/bin/bash
# Script para iniciar el sistema Spotifice con Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Spotifice - Nivel Intermedio (Docker)  "
echo "=========================================="
echo ""

# Paso 1: Construir imágenes
echo "[1/4] Construyendo imágenes Docker..."
docker-compose build

# Paso 2: Iniciar contenedores
echo "[2/4] Iniciando contenedores..."
docker-compose up -d

# Paso 3: Esperar a que el registry esté listo
echo "[3/4] Esperando a que IceGrid Registry esté listo..."
sleep 5

# Verificar que el registry está funcionando
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec icegrid-registry icegridadmin \
        --Ice.Default.Locator="IceGrid/Locator:tcp -h 172.20.0.2 -p 4061" \
        -e "registry list" 2>/dev/null; then
        echo "Registry está listo!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Esperando al registry... intento $RETRY_COUNT/$MAX_RETRIES"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: No se pudo conectar al registry"
    exit 1
fi

# Paso 4: Desplegar la aplicación
echo "[4/4] Desplegando aplicación Spotifice..."
docker exec icegrid-registry icegridadmin \
    --Ice.Default.Locator="IceGrid/Locator:tcp -h 172.20.0.2 -p 4061" \
    -e "application add /app/icegrid/application.xml"

echo ""
echo "=========================================="
echo "  Sistema iniciado correctamente!        "
echo "=========================================="
echo ""
echo "Servidores desplegados:"
echo "  - MediaServer1 en node1 (172.20.0.10)"
echo "  - MediaServer2 en node2 (172.20.0.20)"
echo "  - MediaRender1 en node1 (172.20.0.10)"
echo "  - MediaRender2 en node2 (172.20.0.20)"
echo ""
echo "Para conectar un cliente, usa el locator:"
echo "  Ice.Default.Locator=IceGrid/Locator:tcp -h localhost -p 4061"
echo ""
echo "Para ver los logs:"
echo "  docker-compose logs -f"
echo ""
echo "Para detener:"
echo "  ./stop-docker.sh"
