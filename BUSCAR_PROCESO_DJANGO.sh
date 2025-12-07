#!/bin/bash
# Script para encontrar cómo está corriendo Django

echo "=== Buscando procesos de Python/Django ==="
ps aux | grep -E "python|gunicorn|django" | grep -v grep

echo ""
echo "=== Buscando servicios de systemd ==="
systemctl list-units --type=service --all | grep -E "gunicorn|django|waygps|miapp"

echo ""
echo "=== Buscando en supervisor ==="
if command -v supervisorctl &> /dev/null; then
    supervisorctl status
else
    echo "Supervisor no está instalado"
fi

echo ""
echo "=== Verificando puertos en uso ==="
netstat -tlnp 2>/dev/null | grep -E ":8000|:8001|:80" || ss -tlnp 2>/dev/null | grep -E ":8000|:8001|:80"

echo ""
echo "=== Verificando configuración de Nginx ==="
if [ -f /etc/nginx/sites-available/waygps ]; then
    echo "Configuración encontrada:"
    grep "proxy_pass" /etc/nginx/sites-available/waygps
fi

