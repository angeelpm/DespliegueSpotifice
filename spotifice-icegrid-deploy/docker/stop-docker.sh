#!/bin/bash
cd "$(dirname "$0")"
echo "🛑 Deteniendo contenedores..."
docker-compose down
echo "✅ Sistema detenido"
