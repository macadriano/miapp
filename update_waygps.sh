#!/bin/bash

# Script de actualización rápida para WayGPS
# Uso: ./update_waygps.sh

APP_DIR="/opt/miapp"
VENV_DIR="$APP_DIR/venv"

echo "===== Iniciando actualización de WayGPS ====="
date

# 1. Ir al directorio
cd $APP_DIR

# 2. Actualizar código
echo ">> Descargando últimos cambios..."
git pull

# 3. Activar entorno virtual
echo ">> Activando entorno virtual..."
source $VENV_DIR/bin/activate

# 4. Instalar dependencias (por si hubo cambios)
echo ">> Verificando dependencias..."
pip install -r requirements.txt

# 5. Migraciones de base de datos
echo ">> Aplicando migraciones..."
python manage.py migrate

# 6. Archivos estáticos (CRÍTICO para cambios de UI)
echo ">> Actualizando archivos estáticos..."
python manage.py collectstatic --noinput

# 7. Reiniciar servicios
echo ">> Reiniciando servicios..."
sudo systemctl restart waygps
sudo systemctl restart gunicorn-waygps

echo "===== Actualización completada ====="
echo "Recuerda limpiar la caché del navegador si no ves los cambios (Ctrl + F5)"
