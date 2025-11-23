FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad ANTES de copiar archivos
RUN adduser --disabled-password --gecos '' appwayuser

# Copiar e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Cambiar propietario del directorio /app
RUN chown -R appwayuser:appwayuser /app

# Cambiar a usuario no-root
USER appwayuser

# Copiar código de la aplicación (ahora como appwayuser)
COPY --chown=appwayuser:appwayuser . /app/

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wayproject.wsgi:application"]
