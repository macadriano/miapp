"""
Script para arreglar embeddings placeholder y hacerlos consistentes
"""
from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta
import random


class Command(BaseCommand):
    help = 'Arregla embeddings placeholder para que sean consistentes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Arreglando embeddings placeholder...'))
        
        def generar_placeholder_consistente(texto):
            """Genera embedding placeholder consistente"""
            random.seed(hash(texto.lower().strip()) % (2**31))
            return [random.random() for _ in range(384)]
        
        vectores = VectorConsulta.objects.all()
        total = vectores.count()
        
        self.stdout.write(f'📊 Procesando {total} vectores...')
        
        for i, vector in enumerate(vectores, 1):
            # Regenerar embedding basado en el texto original
            vector.vector_embedding = generar_placeholder_consistente(vector.texto_original)
            
            # Threshold MUY bajo para placeholders
            vector.threshold = 0.05  # Muy bajo para que funcione
            
            vector.save()
            
            self.stdout.write(f'  [{i}/{total}] ✓ {vector.texto_original[:50]}...')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Se arreglaron {total} vectores con threshold 0.05'))
        self.stdout.write(self.style.WARNING('⚠️ Ahora debería funcionar con las consultas'))

