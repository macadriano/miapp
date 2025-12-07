"""
Bot de Telegram para Sofia IA
Integra Sofia con Telegram para responder consultas desde grupos
"""
import os
import django
import logging
import json
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from django.conf import settings
from decouple import config
from asgiref.sync import sync_to_async

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from agenteIA.views import procesar_consulta
from django.test import RequestFactory
from django.http import JsonResponse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración del bot
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_ALLOWED_GROUP_IDS = config('TELEGRAM_ALLOWED_GROUP_IDS', default='', cast=lambda v: [int(x.strip()) for x in v.split(',') if x.strip()])
TELEGRAM_BOT_USERNAME = config('TELEGRAM_BOT_USERNAME', default='')

# Factory para crear requests de Django
factory = RequestFactory()


class SofiaTelegramBot:
    """Bot de Telegram para Sofia IA"""
    
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en el archivo .env")
        
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
        logger.info("✅ Bot de Telegram inicializado")
    
    def setup_handlers(self):
        """Configurar handlers del bot"""
        # Comando /start
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Comando /help
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Comando /status
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Handler para mensajes de texto (solo en grupos permitidos)
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        logger.info("✅ Handlers configurados")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start"""
        welcome_message = (
            "👋 ¡Hola! Soy Sofia, tu asistente de WayGPS.\n\n"
            "Puedo ayudarte con:\n"
            "• Ubicación de vehículos\n"
            "• Recorridos históricos\n"
            "• Tiempo de llegada estimado\n"
            "• Móviles cercanos a un punto\n"
            "• Estado de la flota\n\n"
            "Solo escribe tu consulta y te responderé. Ejemplo:\n"
            "• \"¿Dónde está CAMION1?\"\n"
            "• \"¿Cuánto tarda CAMION2 en llegar a Depósito 3?\"\n"
            "• \"Móviles más cercanos\"\n\n"
            "Usa /help para más información."
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /help"""
        help_message = (
            "📚 **Comandos disponibles:**\n\n"
            "/start - Mensaje de bienvenida\n"
            "/help - Muestra esta ayuda\n"
            "/status - Estado del bot\n\n"
            "💬 **Ejemplos de consultas:**\n\n"
            "• \"¿Dónde está CAMION1?\"\n"
            "• \"¿Cuánto tarda CAMION2 en llegar a Depósito 3?\"\n"
            "• \"Móviles más cercanos a Zona Norte\"\n"
            "• \"Recorrido de AUTO5 de ayer\"\n"
            "• \"¿Qué móviles están en línea?\"\n\n"
            "Solo escribe tu pregunta y Sofia te responderá automáticamente."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /status"""
        status_message = (
            "✅ **Estado del Bot:**\n\n"
            "🟢 Bot activo y funcionando\n"
            "🤖 Sofia IA conectada\n"
            "📡 Sistema operativo\n\n"
            "El bot está listo para recibir consultas."
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    def is_allowed_group(self, chat_id: int) -> bool:
        """Verifica si el grupo está permitido"""
        if not TELEGRAM_ALLOWED_GROUP_IDS:
            # Si no hay grupos configurados, permitir todos (solo para desarrollo)
            logger.warning("⚠️ TELEGRAM_ALLOWED_GROUP_IDS no configurado - permitiendo todos los grupos")
            return True
        return chat_id in TELEGRAM_ALLOWED_GROUP_IDS
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto del grupo"""
        message = update.message
        
        # Ignorar si no hay mensaje
        if not message or not message.text:
            return
        
        chat_id = message.chat.id
        user = message.from_user
        text = message.text.strip()
        
        # Ignorar mensajes vacíos
        if not text:
            return
        
        # Ignorar mensajes del propio bot
        if user and user.is_bot:
            return
        
        # Verificar si es un grupo permitido
        if message.chat.type in ['group', 'supergroup']:
            if not self.is_allowed_group(chat_id):
                logger.info(f"⚠️ Mensaje de grupo no permitido: {chat_id}")
                return
        
        # Mostrar que está procesando
        try:
            processing_msg = await message.reply_text("🤔 Procesando tu consulta...")
        except Exception as e:
            logger.error(f"Error enviando mensaje de procesamiento: {e}")
            processing_msg = None
        
        try:
            # Función wrapper para procesar consulta con sesión inicializada
            def procesar_consulta_con_sesion(mensaje_texto):
                """Procesa una consulta inicializando la sesión en el request"""
                # Crear request de Django
                req = factory.post(
                    '/agenteIA/api/procesar-consulta/',
                    data=json.dumps({'mensaje': mensaje_texto, 'modo': 'texto'}),
                    content_type='application/json'
                )
                
                # Inicializar sesión en el request (necesario para procesar_consulta)
                middleware = SessionMiddleware(lambda r: None)
                middleware.process_request(req)
                req.session.save()
                
                # Procesar consulta
                return procesar_consulta(req)
            
            # Procesar consulta usando la función wrapper (con sync_to_async)
            procesar_consulta_async = sync_to_async(procesar_consulta_con_sesion, thread_sensitive=False)
            response = await procesar_consulta_async(text)
            
            # Obtener respuesta
            if isinstance(response, JsonResponse):
                response_data = json.loads(response.content.decode('utf-8'))
                respuesta = response_data.get('respuesta', 'No se pudo procesar la consulta')
                success = response_data.get('success', False)
                google_maps_link = response_data.get('google_maps_link', None)
                datos_consulta = response_data.get('datos_consulta', {})
                tipo_consulta = datos_consulta.get('tipo_consulta', '')
            else:
                respuesta = "Error al procesar la consulta"
                success = False
                google_maps_link = None
                tipo_consulta = ''
            
            # Limpiar mensaje de procesamiento
            if processing_msg:
                try:
                    await processing_msg.delete()
                except Exception as e:
                    logger.warning(f"No se pudo eliminar mensaje de procesamiento: {e}")
            
            # Enviar respuesta
            if success:
                # Limpiar respuesta para Telegram (remover emojis problemáticos si es necesario)
                respuesta_limpia = respuesta
                
                # Si hay un link de Google Maps (especialmente para VER_MAPA), crear botón inline
                reply_markup = None
                if google_maps_link and tipo_consulta == 'VER_MAPA':
                    # Reemplazar el texto "Abrir Google Maps..." con texto más descriptivo
                    respuesta_limpia = respuesta_limpia.replace(
                        "Abrir Google Maps",
                        "Ver en Google Maps"
                    )
                    # Crear botón inline que abre el enlace directamente
                    keyboard = [[InlineKeyboardButton("🗺️ Abrir en Google Maps", url=google_maps_link)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Si la respuesta es muy larga, dividirla en partes
                max_length = 4096  # Límite de Telegram
                if len(respuesta_limpia) > max_length:
                    # Dividir en chunks
                    chunks = [respuesta_limpia[i:i+max_length] for i in range(0, len(respuesta_limpia), max_length)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            # Solo agregar el botón al primer mensaje
                            await message.reply_text(
                                chunk, 
                                parse_mode='Markdown', 
                                disable_web_page_preview=False,
                                reply_markup=reply_markup
                            )
                            reply_markup = None  # No agregar botón a los mensajes siguientes
                        else:
                            await message.reply_text(f"_(continuación)_\n\n{chunk}", parse_mode='Markdown')
                else:
                    await message.reply_text(
                        respuesta_limpia, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=False,
                        reply_markup=reply_markup
                    )
                
                logger.info(f"✅ Consulta procesada exitosamente: {text[:50]}...")
            else:
                await message.reply_text(
                    f"❌ {respuesta}\n\n"
                    "Intenta reformular tu consulta o usa /help para ver ejemplos."
                )
                logger.warning(f"⚠️ Consulta no procesada correctamente: {text[:50]}...")
        
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
            
            # Limpiar mensaje de procesamiento
            if processing_msg:
                try:
                    await processing_msg.delete()
                except:
                    pass
            
            # Enviar mensaje de error
            error_message = (
                "❌ Ocurrió un error al procesar tu consulta.\n\n"
                "Por favor, intenta nuevamente o contacta al administrador."
            )
            try:
                await message.reply_text(error_message)
            except Exception as e2:
                logger.error(f"Error enviando mensaje de error: {e2}")
    
    def run(self):
        """Inicia el bot"""
        logger.info("🚀 Iniciando bot de Telegram...")
        logger.info(f"📱 Bot username: @{TELEGRAM_BOT_USERNAME or 'N/A'}")
        logger.info(f"👥 Grupos permitidos: {TELEGRAM_ALLOWED_GROUP_IDS or 'Todos (desarrollo)'}")
        
        # Iniciar polling
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


def main():
    """Función principal para ejecutar el bot"""
    try:
        bot = SofiaTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()

