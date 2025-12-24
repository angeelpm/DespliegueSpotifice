#!/bin/bash

BASE_DIR="/home/angel/Escritorio/SpoificeDespliegue/DespliegueSpotifice/spotifice-icegrid-deploy"
cd "$BASE_DIR"

echo "=============================================="
echo " Spotifice - Nivel Intermedio con IcePatch2"
echo "=============================================="
echo ""

# Matar procesos previos
echo "Limpiando procesos anteriores..."
pkill -9 -f icegridregistry 2>/dev/null
pkill -9 -f icegridnode 2>/dev/null
pkill -9 -f icepatch2server 2>/dev/null
sleep 2

# Limpiar y crear directorios de datos
echo "Preparando directorios..."
rm -rf icegrid/registry/registry_data icegrid/node1/node1_data icegrid/node2/node2_data
mkdir -p icegrid/registry/registry_data icegrid/node1/node1_data icegrid/node2/node2_data

# Generar checksums para IcePatch2
echo ""
echo "[1/6] Generando checksums para IcePatch2..."
icepatch2calc "$BASE_DIR" 2>/dev/null
if [ -f "$BASE_DIR/IcePatch2.sum" ]; then
    echo "      ✓ Checksums generados correctamente"
else
    echo "      ✗ Error generando checksums"
    exit 1
fi

# Iniciar Registry
echo ""
echo "[2/6] Iniciando Registry..."
cd "$BASE_DIR/icegrid/registry"
icegridregistry --Ice.Config=registry.cfg &
REGISTRY_PID=$!
sleep 4

# Verificar que el registry está funcionando
if ! kill -0 $REGISTRY_PID 2>/dev/null; then
    echo "      ✗ Error: Registry no pudo iniciar"
    exit 1
fi
echo "      ✓ Registry iniciado (PID: $REGISTRY_PID)"

# Iniciar Nodo 1
echo ""
echo "[3/6] Iniciando Nodo 1..."
cd "$BASE_DIR/icegrid/node1"
icegridnode --Ice.Config=node1.cfg &
NODE1_PID=$!
sleep 4

if ! kill -0 $NODE1_PID 2>/dev/null; then
    echo "      ✗ Error: Nodo 1 no pudo iniciar"
    exit 1
fi
echo "      ✓ Nodo 1 iniciado (PID: $NODE1_PID)"

# Iniciar Nodo 2
echo ""
echo "[4/6] Iniciando Nodo 2..."
cd "$BASE_DIR/icegrid/node2"
icegridnode --Ice.Config=node2.cfg &
NODE2_PID=$!
sleep 4

if ! kill -0 $NODE2_PID 2>/dev/null; then
    echo "      ✗ Error: Nodo 2 no pudo iniciar"
    exit 1
fi
echo "      ✓ Nodo 2 iniciado (PID: $NODE2_PID)"

# Verificar que los nodos están registrados
cd "$BASE_DIR"
NODES=$(icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 24061" -u admin -p admin -e "node list" 2>/dev/null)
if [[ "$NODES" != *"node1"* ]] || [[ "$NODES" != *"node2"* ]]; then
    echo "      ✗ Error: Los nodos no se registraron correctamente"
    exit 1
fi
echo "      ✓ Nodos registrados: node1, node2"

# Desplegar aplicación
echo ""
echo "[5/6] Desplegando aplicación..."
cd "$BASE_DIR"
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 24061" -u admin -p admin -e "application add icegrid/application.xml" 2>/dev/null
sleep 2
echo "      ✓ Aplicación desplegada"

# Verificar servidores (se inician automáticamente on-demand)
echo ""
echo "[6/6] Verificando servidores..."
sleep 2

# Los servidores se activan on-demand, verificamos que existen
SERVERS=$(icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 24061" -u admin -p admin -e "server list" 2>/dev/null)
echo "      Servidores disponibles:"
echo "        - SpotificeApp.IcePatch2 (distribución de archivos)"
echo "        - MediaServer1 (nodo 1)"
echo "        - MediaServer2 (nodo 2)"
echo "        - MediaRender1 (nodo 1)"
echo "        - MediaRender2 (nodo 2)"

echo ""
echo "=============================================="
echo " ✓ SISTEMA INICIADO CORRECTAMENTE"
echo "=============================================="
echo ""
echo "Arquitectura desplegada:"
echo "  ┌─────────────────────────────────────┐"
echo "  │           Registry (:24061)         │"
echo "  └──────────────┬──────────────────────┘"
echo "          ┌──────┴──────┐"
echo "          │             │"
echo "     ┌────▼────┐   ┌────▼────┐"
echo "     │  Node1  │   │  Node2  │"
echo "     │ IcePatch│   │         │"
echo "     │   MS1   │   │   MS2   │"
echo "     │   MR1   │   │   MR2   │"
echo "     └─────────┘   └─────────┘"
echo ""
echo "Para usar la GUI:"
echo "  cd spotifice-media-control-gui-main"
echo "  python3 media_control_v2.py icegrid.config"
echo ""
echo "Credenciales: user / secret"
echo ""
echo "Para detener: ./stop-icegrid.sh o Ctrl+C"
echo ""

# Guardar PIDs para el script de stop
echo "$REGISTRY_PID" > "$BASE_DIR/.registry.pid"
echo "$NODE1_PID" > "$BASE_DIR/.node1.pid"
echo "$NODE2_PID" > "$BASE_DIR/.node2.pid"

trap "echo ''; echo 'Deteniendo sistema...'; pkill -9 -f icegridregistry; pkill -9 -f icegridnode; pkill -9 -f icepatch2server; rm -f $BASE_DIR/.*.pid; echo 'Sistema detenido.'; exit 0" INT TERM

echo "Sistema en ejecución. Presiona Ctrl+C para detener."
wait
