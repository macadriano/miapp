"""
Comando de Django para ejecutar el bot de Telegram de Sofia
Uso: python manage.py run_telegram_bot
"""
from django.core.management.base import BaseCommand
from agenteIA.telegram_bot import SofiaTelegramBot
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ejecuta el bot de Telegram de Sofia IA'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando bot de Telegram de Sofia...'))
        
        try:
            bot = SofiaTelegramBot()
            bot.run()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('🛑 Bot detenido por el usuario'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            logger.error(f"Error ejecutando bot: {e}", exc_info=True)
            raise

