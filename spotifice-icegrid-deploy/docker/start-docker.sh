#!/bin/bash
# ============================================
# Iniciar Spotifice - Nivel Intermedio
# ============================================

set -e
cd "$(dirname "$0")"

LOCATOR="Spotifice/Locator:tcp -h 172.20.0.2 -p 4061"

echo "=========================================="
echo "  Spotifice - Nivel Intermedio (Docker)  "
echo "=========================================="
echo ""

# Limpiar contenedores anteriores
echo "🧹 Limpiando contenedores anteriores..."
docker-compose down 2>/dev/null || true

# Iniciar contenedores
echo "🚀 Iniciando contenedores..."
docker-compose up -d

# Esperar a que el registry esté listo
echo "⏳ Esperando a que el Registry esté listo..."
sleep 5

# Verificar que el registry responde
echo "🔍 Verificando conexión al Registry..."
for i in {1..10}; do
    if icegridadmin --Ice.Default.Locator="$LOCATOR" -u user -p "" -e "registry list" 2>/dev/null | grep -q Master; then
        echo "✅ Registry funcionando"
        break
    fi
    echo "   Intento $i/10..."
    sleep 3
done

# Esperar a que los nodos se conecten
echo "⏳ Esperando a que los nodos se conecten..."
sleep 5

# Desplegar la aplicación
echo ""
echo "📋 Desplegando aplicación Spotifice..."
icegridadmin --Ice.Default.Locator="$LOCATOR" -u user -p "" \
    -e "application remove Spotifice" 2>/dev/null || true

icegridadmin --Ice.Default.Locator="$LOCATOR" -u user -p "" \
    -e "application add config/application.xml"

# Mostrar estado
echo ""
echo "=========================================="
echo "  ✅ Sistema iniciado correctamente!     "
echo "=========================================="
echo ""
echo "📊 Contenedores:"
docker-compose ps
echo ""
echo "📋 Servidores disponibles:"
icegridadmin --Ice.Default.Locator="$LOCATOR" -u user -p "" -e "server list"
echo ""
echo "📋 Nodos conectados:"
icegridadmin --Ice.Default.Locator="$LOCATOR" -u user -p "" -e "node list"
echo ""
echo "🎮 Para administrar:"
echo "   icegridadmin --Ice.Default.Locator='$LOCATOR' -u user -p ''"
echo ""
echo "🛑 Para detener:"
echo "   ./stop-docker.sh"
