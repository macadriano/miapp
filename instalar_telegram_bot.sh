#!/bin/bash xx

echo "===== Instalación del Bot de Telegram para Sofia ====="

APP_DIR="/opt/miapp"
VENV_DIR="$APP_DIR/venv"

# Verificar que estamos en el directorio correcto
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: No existe $APP_DIR"
    exit 1
fi

cd $APP_DIR

# Activar entorno virtual
echo ">> Activando entorno virtual..."
source $VENV_DIR/bin/activate

# Instalar dependencias
echo ">> Instalando python-telegram-bot..."
pip install python-telegram-bot==21.9

# Verificar que existe el archivo .env
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️  ADVERTENCIA: No existe el archivo .env"
    echo "   Por favor, crea el archivo .env con las siguientes variables:"
    echo "   TELEGRAM_BOT_TOKEN=tu_token_aqui"
    echo "   TELEGRAM_BOT_USERNAME=tu_bot_username"
    echo "   TELEGRAM_ALLOWED_GROUP_IDS=-1001234567890"
    exit 1
fi

# Verificar que las variables están configuradas
source $APP_DIR/.env
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  ADVERTENCIA: TELEGRAM_BOT_TOKEN no está configurado en .env"
    echo "   Por favor, agrega: TELEGRAM_BOT_TOKEN=tu_token_aqui"
    exit 1
fi

# Copiar servicio systemd
echo ">> Instalando servicio systemd..."
sudo cp $APP_DIR/telegram-bot-waygps.service /etc/systemd/system/

# Recargar systemd
echo ">> Recargando systemd..."
sudo systemctl daemon-reload

# Habilitar servicio
echo ">> Habilitando servicio..."
sudo systemctl enable telegram-bot-waygps

# Iniciar servicio
echo ">> Iniciando servicio..."
sudo systemctl start telegram-bot-waygps

# Esperar un momento
sleep 2

# Verificar estado
echo ""
echo ">> Estado del servicio:"
sudo systemctl status telegram-bot-waygps --no-pager

echo ""
echo "✅ Instalación completada!"
echo ""
echo "Para ver los logs en tiempo real:"
echo "  sudo journalctl -u telegram-bot-waygps -f"
echo ""
echo "Para reiniciar el bot:"
echo "  sudo systemctl restart telegram-bot-waygps"
echo ""
echo "Para detener el bot:"
echo "  sudo systemctl stop telegram-bot-waygps"
echo ""

