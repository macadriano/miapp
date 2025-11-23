"""
Comando para generar embeddings reales usando sentence-transformers
"""
from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta
import sys

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


class Command(BaseCommand):
    help = 'Genera embeddings reales para todos los vectores usando sentence-transformers'

    def handle(self, *args, **options):
        if not ST_AVAILABLE:
            self.stdout.write(self.style.ERROR('❌ sentence-transformers no está instalado'))
            self.stdout.write(self.style.WARNING('Instala con: pip install sentence-transformers'))
            return
        
        self.stdout.write(self.style.SUCCESS('🔄 Generando embeddings reales...'))
        
        # Cargar modelo
        try:
            self.stdout.write('📥 Descargando modelo (esto puede tardar en primera vez)...')
            modelo = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.stdout.write(self.style.SUCCESS('✅ Modelo cargado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error cargando modelo: {e}'))
            return
        
        # Procesar todos los vectores
        vectores = VectorConsulta.objects.all()
        total = vectores.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️ No hay vectores para procesar'))
            return
        
        self.stdout.write(f'📊 Procesando {total} vectores...')
        
        for i, vector in enumerate(vectores, 1):
            try:
                # Generar embedding real
                embedding = modelo.encode(
                    vector.texto_original,
                    convert_to_numpy=True
                )
                
                # Guardar
                vector.vector_embedding = embedding.tolist()
                
                # Ajustar threshold para embeddings reales
                # Estos embeddings son mucho mejores, podemos usar un threshold normal
                if vector.categoria == 'saludo':
                    vector.threshold = 0.75
                else:
                    vector.threshold = 0.80
                
                vector.save()
                
                self.stdout.write(
                    f'  [{i}/{total}] ✓ {vector.texto_original[:50]}... '
                    f'(similitud mín: {vector.threshold})'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error en vector {vector.id}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Se generaron embeddings reales para {total} vectores'))
        self.stdout.write(self.style.WARNING('\n⚠️ Ahora Sofia usará IA real para procesar las consultas!'))

