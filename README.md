# Spotifice - Nivel Intermedio con IcePatch2

Ángel Pinardo Morollón & Rubén Calzado Chachón.

Despliegue de Spotifice con IceGrid, 2 nodos independientes y distribución de archivos con IcePatch2.

## Arquitectura

```
┌─────────────────────────────────────┐
│         Registry (:24061)           │
└──────────────┬──────────────────────┘
        ┌──────┴──────┐
        │             │
   ┌────▼────┐   ┌────▼────┐
   │  Node1  │   │  Node2  │
   │ IcePatch│   │         │
   │   MS1   │   │   MS2   │
   │   MR1   │   │   MR2   │
   └─────────┘   └─────────┘
```

- **IcePatch2**: Distribución automática de archivos
- **MediaServer1/2**: Servidores de contenido
- **MediaRender1/2**: Reproductores de audio

---

## 1. INICIAR EL SISTEMA

```bash
./start-icegrid.sh &
```

---

## 2. ABRIR LA GUI

```bash
cd spotifice-media-control-gui-main
python3 media_control_v2.py icegrid.config
```

**Credenciales:**
- Usuario: `user`
- Password: `secret`

---

## 3. VER LOGS DE LOS NODOS

> **Nota:** Los logs solo existen después de iniciar el sistema con `./start-icegrid.sh`

**Terminal para logs del Nodo 1:**
```bash
tail -f icegrid/node1/node1_data/servers/MediaServer1/distrib/MediaServer1.err
```

**Terminal para logs del Nodo 2:**
```bash
tail -f icegrid/node2/node2_data/servers/MediaServer2/distrib/MediaServer2.err
```

---

## 4. VERIFICAR SERVIDORES

```bash
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 24061" -u admin -p admin -e "server list"
```

Ver estado de cada servidor:
```bash
icegridadmin --Ice.Default.Locator="SpotificeGrid/Locator:tcp -h localhost -p 24061" -u admin -p admin \
    -e "server state MediaServer1" \
    -e "server state MediaServer2" \
    -e "server state MediaRender1" \
    -e "server state MediaRender2"
```

---

## 5. DETENER TODO EL SISTEMA

Para detener completamente:
```bash
./stop-icegrid.sh
```

---
