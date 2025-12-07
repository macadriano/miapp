#!/bin/bash

# Script para corregir el servicio gunicorn-waygps
# Soluciona el error de LimitNOFILE y el puerto en uso

APP_DIR="/opt/miapp"
VENV_DIR="$APP_DIR/venv"
DJANGO_SETTINGS="wayproject.settings"

echo "===== Corrigiendo servicio Gunicorn WayGPS ====="

# 1. Detener el servicio actual
echo ">> Deteniendo servicio gunicorn-waygps..."
sudo systemctl stop gunicorn-waygps 2>/dev/null

# 2. Encontrar y matar procesos que usan el puerto 8000
echo ">> Buscando procesos en puerto 8000..."
PID_8000=$(sudo lsof -ti:8000 2>/dev/null || sudo fuser 8000/tcp 2>/dev/null | awk '{print $2}')

if [ ! -z "$PID_8000" ]; then
    echo ">> Proceso encontrado en puerto 8000: PID $PID_8000"
    echo ">> Deteniendo proceso..."
    sudo kill -9 $PID_8000 2>/dev/null
    sleep 2
    echo ">> Proceso detenido"
else
    echo ">> No se encontraron procesos en puerto 8000"
fi

# 3. Crear archivo de servicio corregido
echo ">> Creando archivo de servicio corregido..."
sudo tee /etc/systemd/system/gunicorn-waygps.service > /dev/null <<EOF
[Unit]
Description=Gunicorn WayGPS Django service
After=network.target
Wants=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment="DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS"
ExecStart=$VENV_DIR/bin/gunicorn wayproject.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always
RestartSec=3

# Límites del sistema (sintaxis correcta)
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

# 4. Recargar systemd
echo ">> Recargando configuración de systemd..."
sudo systemctl daemon-reload

# 5. Habilitar y reiniciar servicio
echo ">> Habilitando servicio..."
sudo systemctl enable gunicorn-waygps

echo ">> Iniciando servicio..."
sudo systemctl start gunicorn-waygps

# 6. Esperar un momento y verificar estado
sleep 3
echo ""
echo ">> Estado del servicio:"
sudo systemctl status gunicorn-waygps --no-pager -l

echo ""
echo "===== Corrección completada ====="
echo "Si el servicio no está corriendo, revisa los logs con:"
echo "  sudo journalctl -u gunicorn-waygps -n 50"

