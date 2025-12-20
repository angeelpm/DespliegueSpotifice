# Spotifice - Nivel Intermedio (Docker)

Despliegue de Spotifice utilizando Docker con 2 nodos IceGrid independientes, simulando máquinas virtuales separadas.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    Red Docker: spotifice-network                │
│                         172.28.0.0/16                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐                                           │
│  │    Registry     │  172.28.0.10:4061                         │
│  │   (IceGrid)     │  Expuesto: localhost:4061                 │
│  └────────┬────────┘                                           │
│           │                                                     │
│     ┌─────┴─────┐                                              │
│     │           │                                               │
│  ┌──▼──┐     ┌──▼──┐                                           │
│  │Node1│     │Node2│   ← Nodos independientes (como VMs)       │
│  │     │     │     │                                            │
│  │ MS1 │     │ MS2 │   MediaServer1, MediaServer2              │
│  │ MR1 │     │ MR2 │   MediaRender1, MediaRender2              │
│  │     │     │     │                                            │
│  └─────┘     └─────┘                                           │
│  172.28.0.11  172.28.0.12                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Requisitos

- Docker (versión 20.10 o superior)
- docker-compose (versión 1.29 o superior) o Docker Compose V2
- Python 3.10+ (para el cliente GUI)
- GTK4 y dependencias de GStreamer (para reproducción de audio en el cliente)

### Instalar Docker en Ubuntu

```bash
# Instalar Docker
sudo apt update
sudo apt install -y docker.io docker-compose

# Iniciar servicio
sudo systemctl start docker
sudo systemctl enable docker

# Añadir usuario al grupo docker (requiere cerrar sesión)
sudo usermod -aG docker $USER
```

## Estructura del despliegue

| Componente | Contenedor | IP | Puerto |
|------------|------------|-----|--------|
| Registry IceGrid | spotifice-registry | 172.28.0.10 | 4061 (expuesto) |
| Nodo 1 | spotifice-node1 | 172.28.0.11 | - |
| Nodo 2 | spotifice-node2 | 172.28.0.12 | - |
| Admin | spotifice-admin | 172.28.0.20 | - |

### Servidores desplegados

- **Nodo 1**: MediaServer1 + MediaRender1 + IcePatch2
- **Nodo 2**: MediaServer2 + MediaRender2

Los servidores están configurados con **grupos de réplica** para balanceo de carga aleatorio.

## Instrucciones de uso

### 1. Iniciar el sistema

```bash
cd docker
./start-docker.sh
```

El script:
1. Verifica que Docker esté instalado y funcionando
2. Construye la imagen base con todas las dependencias
3. Inicia los contenedores (Registry, Node1, Node2, Admin)
4. Despliega la aplicación Spotifice
5. Inicia los 4 servidores automáticamente

### 2. Iniciar MediaRender local (para reproducir audio)

**IMPORTANTE**: Los MediaRender en Docker no pueden reproducir audio en tu ordenador. 
Necesitas ejecutar un MediaRender local:

En una **nueva terminal**:

```bash
cd docker
./run-local-render.sh
```

Deja esta terminal abierta mientras usas la aplicación.

### 3. Usar la aplicación (GUI)

En **otra terminal**:

```bash
cd spotifice-media-control-gui-main
python3 media_control_v2.py ../docker/client-local-render.config
```

**Credenciales:**
- Usuario: `user`
- Password: `secret`

> **Nota**: Usa `client-local-render.config` para conectarte al MediaRender local que tiene acceso al audio de tu ordenador.

### 4. Verificar el estado

```bash
# Ver estado de contenedores
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker logs spotifice-node1
docker logs spotifice-node2
```

### 4. Administrar IceGrid

```bash
# Conectar al admin de IceGrid
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 4061" -u admin -p admin

# Comandos útiles dentro de icegridadmin:
server list                    # Listar servidores
server state MediaServer1      # Ver estado de un servidor
node list                      # Listar nodos
application describe SpotificeApp  # Ver descripción de la aplicación
```

### 5. Detener el sistema

```bash
cd docker
./stop-docker.sh
```

Para eliminar también los datos persistentes:
```bash
docker compose down -v
```

## IcePatch2 - Distribución de aplicación

El Nodo 1 incluye un servidor IcePatch2 que permite distribuir actualizaciones de la aplicación a otros nodos. Esto cumple con el requisito del nivel intermedio de usar IcePatch2 para el despliegue.

## Demostración de uso de múltiples servidores

Para demostrar que se usan todos los servidores desplegados:

1. Conecta múltiples clientes GUI
2. Cada conexión puede ser atendida por un MediaServer diferente (balanceo aleatorio)
3. Los MediaRender también se distribuyen entre los disponibles

Puedes verificar qué servidor está atendiendo cada petición observando los logs:
```bash
docker logs -f spotifice-node1
docker logs -f spotifice-node2
```

## Diferencias con Nivel Básico

| Aspecto | Nivel Básico | Nivel Intermedio |
|---------|--------------|------------------|
| Nodos | 2 procesos locales | 2 contenedores Docker independientes |
| Aislamiento | Mismo sistema | Red aislada, sistemas separados |
| Servidores | 2 MS + 2 MR | 2 MS + 2 MR + IcePatch2 |
| Despliegue | Script bash | Docker Compose |
| Portabilidad | Depende del sistema | Reproducible en cualquier máquina |

## Troubleshooting

### Error: Puerto 4061 en uso
```bash
# Verificar qué usa el puerto
sudo lsof -i :4061

# Detener el servicio IceGrid del sistema si existe
sudo systemctl stop icegridregistry
```

### Error: Permisos de Docker
```bash
# Añadir usuario al grupo docker
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### Contenedores no inician
```bash
# Ver logs detallados
docker compose logs

# Reconstruir imágenes
docker compose build --no-cache
```
