"""
Comando para descargar y configurar el modelo de sentence-transformers offline
"""
from django.core.management.base import BaseCommand
import os
import sys


class Command(BaseCommand):
    help = 'Descarga el modelo de sentence-transformers para uso offline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-dir',
            type=str,
            default=None,
            help='Directorio donde guardar el modelo (default: .cache/models)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar re-descarga del modelo aunque ya exista',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Iniciando descarga del modelo de sentence-transformers...'))
        
        try:
            from sentence_transformers import SentenceTransformer
            ST_AVAILABLE = True
        except ImportError:
            self.stdout.write(self.style.ERROR('❌ sentence-transformers no está instalado'))
            self.stdout.write(self.style.WARNING('Instala con: pip install sentence-transformers'))
            return
        
        # Determinar directorio de caché
        cache_dir = options.get('cache_dir')
        if not cache_dir:
            cache_dir = os.path.join(os.getcwd(), '.cache', 'models')
        
        os.makedirs(cache_dir, exist_ok=True)
        self.stdout.write(f'📁 Directorio de caché: {cache_dir}')
        
        # Verificar si el modelo ya existe
        model_path = os.path.join(cache_dir, 'sentence-transformers_paraphrase-multilingual-MiniLM-L12-v2')
        
        if os.path.exists(model_path) and not options.get('force'):
            self.stdout.write(self.style.WARNING(f'✅ El modelo ya existe en {model_path}'))
            self.stdout.write(self.style.WARNING('Usa --force para re-descargar'))
            return
        
        # Descargar el modelo
        try:
            self.stdout.write('📥 Descargando modelo de Hugging Face (esto puede tardar)...')
            self.stdout.write('🌐 Asegúrate de tener conexión a internet')
            
            modelo = SentenceTransformer(
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                cache_folder=cache_dir
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Modelo descargado exitosamente'))
            self.stdout.write(f'📁 Ubicación: {cache_dir}')
            self.stdout.write('')
            self.stdout.write('💡 El modelo ahora está disponible offline')
            self.stdout.write('🔄 Sofia lo usará automáticamente en próximas ejecuciones')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error descargando modelo: {e}'))
            self.stdout.write(self.style.WARNING('Verifica tu conexión a internet'))
            return

