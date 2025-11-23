from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta
import random


def generar_placeholder(texto: str) -> list:
    """Replica el embedding determinístico utilizado por el vectorizador placeholder."""
    random.seed(hash(texto) % 2**32)
    return [random.random() for _ in range(384)]


class Command(BaseCommand):
    help = "Regenera embeddings determinísticos para consultas de cercanía"

    def handle(self, *args, **options):
        consultas = VectorConsulta.objects.filter(tipo_consulta='CERCANIA')
        total = consultas.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No se encontraron consultas de cercanía.'))
            return

        self.stdout.write(f"Actualizando {total} vectores de cercanía...")
        for consulta in consultas:
            nuevo_embedding = generar_placeholder(consulta.texto_original)
            consulta.vector_embedding = nuevo_embedding
            if consulta.threshold is None or consulta.threshold > 0.5:
                consulta.threshold = 0.3
            consulta.save(update_fields=['vector_embedding', 'threshold', 'updated_at'])

        self.stdout.write(self.style.SUCCESS('Embeddings de cercanía regenerados correctamente.'))
