#!/bin/bash
# Script para detener el entorno Docker de Spotifice

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Deteniendo contenedores Spotifice..."

# Determinar el comando de compose
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

$COMPOSE_CMD down

echo "Sistema detenido."
echo ""
echo "Para eliminar también los volúmenes de datos:"
echo "  $COMPOSE_CMD down -v"
