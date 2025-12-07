#!/bin/bash
# Script para reiniciar completamente Django y limpiar caché

echo "=== Limpiando procesos Django ==="
pkill -f "python.*manage.py" 2>/dev/null
pkill -f gunicorn 2>/dev/null
pkill -f uwsgi 2>/dev/null
sleep 2

echo "=== Limpiando archivos .pyc ==="
find /opt/miapp -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
find /opt/miapp -type f -name "*.pyc" -delete 2>/dev/null

echo "=== Verificando archivos ==="
ls -la /opt/miapp/templates/partials/sidebar.html

echo "=== Verificando contenido ==="
grep -E "Dashboard2|Móviles2" /opt/miapp/templates/partials/sidebar.html

echo "=== Reiniciando Nginx ==="
sudo nginx -s reload

echo "=== Listo. Reinicia Django manualmente según tu configuración ==="
echo "Ejemplo: cd /opt/miapp && source venv/bin/activate && python manage.py runserver"

