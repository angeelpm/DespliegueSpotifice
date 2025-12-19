# Spotifice con IceGrid - Nivel Básico

Despliegue de Spotifice utilizando IceGrid con 2 nodos en la misma máquina.

## Requisitos

- Python ≥ 3.10
- ZeroC Ice 3.7
- GStreamer (para reproducción de audio)
- GTK4 (para la interfaz gráfica)

## Estructura del despliegue

- **Registry IceGrid**: Puerto 4061
- **Nodo 1 (node1)**: Ejecuta MediaServer1 y MediaRender1
- **Nodo 2 (node2)**: Ejecuta MediaServer2 y MediaRender2
- **Grupos de réplicas**: Con balanceo de carga aleatorio
- **Activación**: On-demand (bajo demanda)

## Instrucciones de uso

### 1. Iniciar el sistema

```bash
./start-icegrid.sh
```

Este script:
- Limpia procesos previos de IceGrid
- Crea directorios de datos necesarios
- Inicia el Registry de IceGrid
- Inicia los nodos 1 y 2
- Despliega la aplicación Spotifice
- Inicia los 4 servidores (2 MediaServer + 2 MediaRender)

El script se quedará ejecutando. Deja esta terminal abierta.

### 2. Usar la aplicación

**Opción A - Interfaz gráfica (recomendado):**

En una nueva terminal:
```bash
cd spotifice-media-control-gui-main
python3 media_control_v2.py icegrid.config
```

**Opción B - Cliente de línea de comandos:**

En una nueva terminal:
```bash
python3 media_control.py client-icegrid.config
```

**Credenciales de prueba:**
- Usuario: `user`
- Contraseña: `secret`

### 3. Detener el sistema

En la terminal donde ejecutaste `start-icegrid.sh`, presiona **Ctrl+C**, o ejecuta:

```bash
./stop-icegrid.sh
```

## Verificación del despliegue

Para comprobar el estado del sistema:

```bash
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 4061" \
    -u admin -p admin \
    -e "server list" \
    -e "node list" \
    -e "server state MediaServer1" \
    -e "server state MediaRender1"
```

Deberías ver:
- 4 servidores: MediaServer1, MediaServer2, MediaRender1, MediaRender2
- 2 nodos: node1, node2
- Estado: active (enabled)

## Archivos de configuración

### Registry (`icegrid/registry/registry.cfg`)
- Puerto del cliente: 4061
- Base de datos LMDB en `registry_data/`
- Permisos de verificación nulos (para desarrollo)

### Nodos (`icegrid/node1/node1.cfg` y `icegrid/node2/node2.cfg`)
- Conectados al Registry en localhost:4061
- Directorios de datos: `node1_data/` y `node2_data/`

### Aplicación (`icegrid/application.xml`)
- Templates para MediaServer y MediaRender
- Grupos de réplicas con balanceo aleatorio
- Activación on-demand
- Directorio de trabajo: `/home/angel/Escritorio/DISTRIBUIDOS/spotifice-icegrid-deploy`

## Playlists disponibles

- `playlists/portal2-vol1.playlist` - 22 canciones
- `playlists/portal2-vol2.playlist` - 26 canciones
- `playlists/portal2-vol3.playlist` - 20 canciones

## Solución de problemas

**Error: "connection refused"**
- Asegúrate de que el Registry está corriendo
- Verifica que el puerto 4061 no esté ocupado: `netstat -tuln | grep 4061`

**Error: "Server not active"**
- Los servidores se activan bajo demanda
- Espera unos segundos y vuelve a intentar

**No hay archivos MP3**
- Ejecuta: `make media` para descargar la banda sonora de Portal 2

## Puntuación

✅ **Nivel Básico: 8 puntos**
- Registry IceGrid
- 2 nodos en la misma máquina
- 2 MediaServer + 2 MediaRender
- Grupos de réplicas con balanceo de carga
- Activación on-demand

## Autores

Desarrollado para Sistemas Distribuidos - UCLM-ESI (2025-2026)
