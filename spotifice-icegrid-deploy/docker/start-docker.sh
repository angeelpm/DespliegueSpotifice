#!/bin/bash
# Script para iniciar el entorno Docker de Spotifice - Nivel Intermedio

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo " Spotifice - Nivel Intermedio (Docker)"
echo "========================================"
echo ""

# Verificar que Docker está instalado y funcionando
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado"
    echo "Instálalo con: sudo apt install docker.io docker-compose"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Docker no está corriendo o no tienes permisos"
    echo "Ejecuta: sudo systemctl start docker"
    echo "O añádete al grupo docker: sudo usermod -aG docker $USER"
    exit 1
fi

# Verificar docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: docker-compose no está instalado"
    echo "Instálalo con: sudo apt install docker-compose"
    exit 1
fi

# Determinar el comando de compose
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "1. Construyendo imagen base..."
$COMPOSE_CMD build --quiet

echo "2. Iniciando contenedores..."
$COMPOSE_CMD up -d

echo "3. Esperando a que el sistema se inicie..."
echo "   (Esto puede tomar 20-30 segundos)"

# Esperar a que el admin termine de desplegar
sleep 5
echo -n "   Registry"
while ! docker logs spotifice-admin 2>&1 | grep -q "Spotifice desplegado correctamente"; do
    echo -n "."
    sleep 2
    # Timeout después de 60 segundos
    if [ $SECONDS -gt 60 ]; then
        echo ""
        echo "ADVERTENCIA: El despliegue está tardando más de lo esperado"
        echo "Revisa los logs con: docker logs spotifice-admin"
        break
    fi
done
echo " ¡Listo!"

echo ""
echo "========================================"
echo " Sistema Spotifice iniciado"
echo "========================================"
echo ""
echo "Servicios desplegados:"
echo "  - Registry IceGrid:  localhost:4061"
echo "  - Nodo 1 (node1):    MediaServer1 + MediaRender1"
echo "  - Nodo 2 (node2):    MediaServer2 + MediaRender2"
echo ""
echo "Para usar la GUI:"
echo "  cd ../spotifice-media-control-gui-main"
echo "  python3 media_control_v2.py ../docker/client-docker.config"
echo ""
echo "Credenciales: user / secret"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:     $COMPOSE_CMD logs -f"
echo "  Estado:       $COMPOSE_CMD ps"
echo "  Detener:      ./stop-docker.sh"
echo ""
