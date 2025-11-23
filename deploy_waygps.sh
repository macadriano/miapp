#!/bin/bash

echo "===== WayGPS - Deploy Automático ====="

APP_DIR="/opt/miapp"
VENV_DIR="$APP_DIR/venv"
DJANGO_SETTINGS="wayproject.settings"
SERVER_IP="200.58.98.187"

echo ">> Verificando directorio del proyecto..."
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: No existe $APP_DIR"
    exit 1
fi

echo ">> Activando entorno virtual..."
source $VENV_DIR/bin/activate

echo ">> Aplicando collectstatic..."
python $APP_DIR/manage.py collectstatic --noinput

echo ">> Creando servicio systemd para Gunicorn..."
cat << EOF | sudo tee /etc/systemd/system/gunicorn-waygps.service
[Unit]
Description=Gunicorn WayGPS Django service
After=network.target docker.service
Requires=docker.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
Environment="DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS"
ExecStart=$VENV_DIR/bin/gunicorn wayproject.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo ">> Habilitando servicio Gunicorn..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-waygps
sudo systemctl restart gunicorn-waygps

echo ">> Instalando Nginx si no está instalado..."
sudo apt install nginx -y

echo ">> Creando configuración Nginx..."
cat << EOF | sudo tee /etc/nginx/sites-available/waygps
server {
    listen 80;
    server_name $SERVER_IP;

    location /static/ {
        alias $APP_DIR/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

echo ">> Activando sitio Nginx..."
sudo ln -s /etc/nginx/sites-available/waygps /etc/nginx/sites-enabled/ 2>/dev/null
sudo rm /etc/nginx/sites-enabled/default 2>/dev/null

echo ">> Probando configuración Nginx..."
sudo nginx -t

echo ">> Reiniciando Nginx..."
sudo systemctl restart nginx

echo "=========================================="
echo " WAYGPS DEPLOY COMPLETADO CORRECTAMENTE"
echo " Acceso público: http://$SERVER_IP/"
echo " Gunicorn corriendo como servicio: gunicorn-waygps"
echo "=========================================="
