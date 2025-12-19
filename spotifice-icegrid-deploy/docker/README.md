# Spotifice - Nivel Intermedio (Docker)

Despliegue de Spotifice usando Docker con IceGrid.

## Arquitectura

```
┌──────────────────────────────────────────────────────┐
│                   Docker Network                      │
│                  172.20.0.0/24                        │
│                                                       │
│  ┌─────────────────┐                                 │
│  │ icegrid-registry│  172.20.0.2:4061                │
│  │ (IceGrid Master)│                                 │
│  └────────┬────────┘                                 │
│           │                                           │
│     ┌─────┴─────┐                                    │
│     │           │                                    │
│  ┌──┴───┐   ┌──┴───┐                                │
│  │node1 │   │node2 │                                │
│  │.0.10 │   │.0.20 │                                │
│  └──┬───┘   └──┬───┘                                │
│     │          │                                     │
│  MediaServer1  MediaServer2                         │
│  MediaRender1  MediaRender2                         │
└──────────────────────────────────────────────────────┘
```

## Requisitos

- Docker y Docker Compose
- ZeroC Ice (icegridadmin) instalado en el host

## Uso Rápido

```bash
# Iniciar el sistema
./start-docker.sh

# Detener el sistema
./stop-docker.sh
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `docker-compose.yml` | Definición de contenedores |
| `Dockerfile.node` | Imagen del nodo con Python |
| `start-docker.sh` | Script de inicio |
| `stop-docker.sh` | Script de parada |
| `client-docker.config` | Configuración para clientes externos |
| `config/registry.cfg` | Configuración del registry |
| `config/node1.cfg` | Configuración del nodo 1 |
| `config/node2.cfg` | Configuración del nodo 2 |
| `config/application.xml` | Descriptor de la aplicación IceGrid |

## Administración

Conectar al admin de IceGrid:
```bash
icegridadmin --Ice.Default.Locator='Spotifice/Locator:tcp -h 172.20.0.2 -p 4061' -u user -p ''
```

Comandos útiles:
```bash
# Listar servidores
server list

# Ver estado de un servidor
server state MediaServer1

# Iniciar/detener servidor
server start MediaServer1
server stop MediaServer1

# Ver nodos
node list
```

## Cliente Externo

Para conectar un cliente externo a este despliegue Docker, usa:

```python
import Ice
Ice.loadSlice('spotifice_v2.ice')
import Spotifice

with Ice.initialize(['--Ice.Config=docker/client-docker.config']) as communicator:
    proxy = communicator.stringToProxy("mediaServer")
    server = Spotifice.MediaServerPrx.checkedCast(proxy)
    # ...
```

## Nivel Intermedio - Características

- ✅ 2 nodos IceGrid
- ✅ 2 MediaServer (réplicas con load balancing)
- ✅ 2 MediaRender (réplicas con load balancing)
- ✅ Replica Groups con round-robin
- ✅ Activación on-demand
