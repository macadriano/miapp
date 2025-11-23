#!/bin/bash
# Script para buscar la ubicación de django-docker-project

echo "🔍 Buscando django-docker-project..."
echo ""

# Buscar en ubicaciones comunes
echo "1. Buscando en /root:"
find /root -name "django-docker-project" -type d 2>/dev/null

echo ""
echo "2. Buscando en /home:"
find /home -name "django-docker-project" -type d 2>/dev/null

echo ""
echo "3. Buscando en /opt:"
find /opt -name "django-docker-project" -type d 2>/dev/null

echo ""
echo "4. Buscando en /var:"
find /var -name "django-docker-project" -type d 2>/dev/null

echo ""
echo "5. Buscando en el directorio actual:"
pwd
ls -la

echo ""
echo "6. Buscando en /:"
find / -maxdepth 3 -name "django-docker-project" -type d 2>/dev/null | head -10

echo ""
echo "7. Verificando si está dentro de Docker:"
docker ps 2>/dev/null | grep -i django || echo "Docker no disponible o sin contenedores Django"

echo ""
echo "8. Listando directorios en /root:"
ls -la /root | head -20
