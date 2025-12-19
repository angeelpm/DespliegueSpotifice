FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libzeroc-ice3.7 \
    zeroc-ice-all-runtime \
    zeroc-ice-all-dev \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libgirepository1.0-dev \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    python3-gi \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir zeroc-ice PyGObject

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de la aplicación
COPY *.py /app/
COPY *.ice /app/
COPY users.json /app/

# Crear directorios necesarios
RUN mkdir -p /app/media /app/playlists /app/icegrid

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Puerto por defecto (se sobrescribirá en docker-compose)
EXPOSE 10000-10100
