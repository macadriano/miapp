#!/bin/bash
# Script de deploy para servidor de producción

echo "🚀 Iniciando deploy de WayGPS..."

# Crear directorio de logs si no existe
mkdir -p logs

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --settings=wayproject.settings_production

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=wayproject.settings_production

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
python manage.py shell --settings=wayproject.settings_production << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@waygps.com', 'admin123')
    print("✅ Superusuario creado: admin/admin123")
else:
    print("ℹ️ Superusuario ya existe")
EOF

echo "✅ Deploy completado!"
echo "🌐 Aplicación disponible en: http://tu-servidor.com:8000"
echo "🔑 Login: admin / admin123"
