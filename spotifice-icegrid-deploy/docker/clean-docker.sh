#!/bin/bash
# Script para limpiar todo (contenedores, imágenes, volúmenes)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Deteniendo y eliminando contenedores..."
docker-compose down -v --rmi all

echo "Limpieza completada"
