#!/bin/bash
# Script para detener el sistema Spotifice con Docker

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Deteniendo contenedores Spotifice..."
docker-compose down

echo "Sistema detenido"
