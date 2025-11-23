"""
Comando para ajustar los thresholds de los vectores
"""
from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta


class Command(BaseCommand):
    help = 'Ajusta los thresholds de los vectores'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Ajustando thresholds...'))
        
        vectores = VectorConsulta.objects.all()
        total = vectores.count()
        
        for i, vector in enumerate(vectores, 1):
            # Ajustar thresholds
            if vector.categoria == 'saludo':
                vector.threshold = 0.60
            elif vector.categoria == 'actual':
                vector.threshold = 0.40
            elif vector.categoria == 'pasado':
                vector.threshold = 0.40
            elif vector.categoria == 'futuro':
                vector.threshold = 0.40
            elif vector.categoria == 'comando':
                vector.threshold = 0.50
            else:
                vector.threshold = 0.40
            
            vector.save()
            
            self.stdout.write(f'  [{i}/{total}] ✓ {vector.texto_original[:50]}... -> {vector.threshold}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Se ajustaron {total} vectores'))
        self.stdout.write(self.style.WARNING('⚠️ Thresholds ajustados a valores más permisivos para embeddings reales'))

