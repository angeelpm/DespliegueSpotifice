#!/bin/bash
# Script para iniciar IceGrid con Spotifice

BASE_DIR="/home/angel/Escritorio/DISTRIBUIDOS/spotifice-icegrid-deploy"
cd "$BASE_DIR"

echo "=== Iniciando Spotifice con IceGrid ==="

# Matar procesos previos
killall icegridnode icegridregistry 2>/dev/null
sleep 1

# Limpiar y crear directorios de datos
rm -rf icegrid/registry/registry_data icegrid/node1/node1_data icegrid/node2/node2_data
mkdir -p icegrid/registry/registry_data icegrid/node1/node1_data icegrid/node2/node2_data

# 1. Iniciar Registry
echo "1. Iniciando Registry..."
cd "$BASE_DIR/icegrid/registry"
icegridregistry --Ice.Config=registry.cfg &
sleep 2

# 2. Iniciar Nodo 1
echo "2. Iniciando Nodo 1..."
cd "$BASE_DIR/icegrid/node1"
icegridnode --Ice.Config=node1.cfg &
sleep 2

# 3. Iniciar Nodo 2
echo "3. Iniciando Nodo 2..."
cd "$BASE_DIR/icegrid/node2"
icegridnode --Ice.Config=node2.cfg &
sleep 2

# 4. Desplegar aplicación
echo "4. Desplegando aplicación..."
cd "$BASE_DIR"
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 4061" -u admin -p admin -e "application add icegrid/application.xml"
sleep 1

# 5. Iniciar servidores
echo "5. Iniciando servidores..."
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 4061" -u admin -p admin \
    -e "server start MediaServer1" \
    -e "server start MediaServer2" \
    -e "server start MediaRender1" \
    -e "server start MediaRender2"

echo ""
echo "=== Sistema iniciado ==="
echo "Para usar el cliente: python3 media_control.py client-icegrid.config"
echo "Para usar la GUI: cd spotifice-media-control-gui-main && python3 media_control_v2.py icegrid.config"
echo "Usuario: user | Password: secret"
echo ""
echo "Presiona Ctrl+C para detener"

trap "killall icegridnode icegridregistry python3 2>/dev/null; exit 0" INT TERM
wait
