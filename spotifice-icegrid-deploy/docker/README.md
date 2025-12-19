# Spotifice - Nivel Intermedio (Docker)

Este directorio contiene la configuración para el despliegue de Spotifice usando Docker, cumpliendo los requisitos del **Nivel Intermedio** del trabajo:

- ✅ 2 nodos IceGrid independientes (contenedores Docker)
- ✅ 2 servidores MediaServer (uno en cada nodo)
- ✅ 2 servidores MediaRender (uno en cada nodo)
- ✅ Distribución con IcePatch2

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Red Docker (172.20.0.0/24)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐                                            │
│  │  IceGrid Registry   │  172.20.0.2:4061                           │
│  │  (icegrid-registry) │                                            │
│  └─────────────────────┘                                            │
│            │                                                        │
│  ┌─────────────────────┐                                            │
│  │   IcePatch2 Server  │  172.20.0.5:4070                           │
│  │   (icepatch-server) │                                            │
│  └─────────────────────┘                                            │
│            │                                                        │
│    ┌───────┴───────┐                                                │
│    │               │                                                │
│    ▼               ▼                                                │
│  ┌─────────────┐ ┌─────────────┐                                    │
│  │   Node 1    │ │   Node 2    │                                    │
│  │ 172.20.0.10 │ │ 172.20.0.20 │                                    │
│  ├─────────────┤ ├─────────────┤                                    │
│  │MediaServer1 │ │MediaServer2 │                                    │
│  │MediaRender1 │ │MediaRender2 │                                    │
│  └─────────────┘ └─────────────┘                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Requisitos

- Docker Engine 20.10+
- Docker Compose v2+

## Inicio Rápido

### 1. Iniciar el sistema

```bash
cd docker
chmod +x *.sh
./start-docker.sh
```

El script:
1. Construye las imágenes Docker
2. Inicia los contenedores (registry, node1, node2, icepatch)
3. Espera a que el registry esté listo
4. Despliega la aplicación Spotifice

### 2. Verificar el despliegue

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Conectar al admin de IceGrid
docker exec -it icegrid-registry icegridadmin \
    --Ice.Default.Locator="IceGrid/Locator:tcp -h 172.20.0.2 -p 4061"
```

Comandos útiles en icegridadmin:
```
server list          # Lista todos los servidores
node list            # Lista todos los nodos
server start MediaServer1
server start MediaServer2
server start MediaRender1
server start MediaRender2
```

### 3. Conectar un cliente

Desde el directorio principal de spotifice-icegrid-deploy:

```bash
# Usando la GUI
cd spotifice-media-control-gui-main
python media_control_v2.py --Ice.Config=../docker/client-docker.config

# O usando el cliente de línea de comandos
python media_control.py --Ice.Config=docker/client-docker.config
```

### 4. Detener el sistema

```bash
./stop-docker.sh
```

### 5. Limpiar todo (incluyendo volúmenes e imágenes)

```bash
./clean-docker.sh
```

## Estructura de Archivos

```
docker/
├── Dockerfile              # Imagen base con Ice y GStreamer
├── docker-compose.yml      # Definición de servicios
├── start-docker.sh         # Script de inicio
├── stop-docker.sh          # Script de parada
├── clean-docker.sh         # Script de limpieza
├── client-docker.config    # Configuración del cliente
└── config/
    ├── registry.cfg        # Configuración del Registry
    ├── node1.cfg           # Configuración del Nodo 1
    ├── node2.cfg           # Configuración del Nodo 2
    ├── icepatch.cfg        # Configuración de IcePatch2
    └── application.xml     # Descriptor de la aplicación
```

## IcePatch2

IcePatch2 se utiliza para distribuir automáticamente los archivos de la aplicación a los nodos. Cuando un nodo se inicia:

1. Se conecta al servidor IcePatch2
2. Descarga/actualiza los archivos necesarios
3. Los almacena en su directorio local

Esto permite actualizar la aplicación sin necesidad de reconstruir las imágenes Docker.

## Demostración de Funcionamiento

Para demostrar que ambos servidores funcionan, puedes:

1. **Iniciar todos los servidores:**
   ```
   icegridadmin> server start MediaServer1
   icegridadmin> server start MediaServer2
   icegridadmin> server start MediaRender1
   icegridadmin> server start MediaRender2
   ```

2. **Conectar cliente a MediaRender1:**
   - Usa el cliente GUI
   - Selecciona mediaRender1
   - Reproduce música

3. **Conectar otro cliente a MediaRender2:**
   - Abre otro terminal
   - Usa el cliente GUI con otro render
   - Reproduce música diferente

Ambos clientes reproducirán simultáneamente, demostrando la capacidad distribuida del sistema.

## Troubleshooting

### Error: "No se puede conectar al registry"
```bash
# Verificar que los contenedores están corriendo
docker-compose ps

# Ver logs del registry
docker-compose logs registry
```

### Error: "Server not found"
```bash
# Verificar que la aplicación está desplegada
docker exec icegrid-registry icegridadmin \
    --Ice.Default.Locator="IceGrid/Locator:tcp -h 172.20.0.2 -p 4061" \
    -e "application list"

# Re-desplegar si es necesario
docker exec icegrid-registry icegridadmin \
    --Ice.Default.Locator="IceGrid/Locator:tcp -h 172.20.0.2 -p 4061" \
    -e "application add /app/icegrid/application.xml"
```

### Reiniciar desde cero
```bash
./clean-docker.sh
./start-docker.sh
```
