from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta
from agenteIA.vectorizador import VectorizadorConsultas

class Command(BaseCommand):
    help = 'Actualiza los intents y vectores de SOFIA con los nuevos comandos'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando actualización de intents de SOFIA...")
        
        vectorizador = VectorizadorConsultas()
        
        # Definición de nuevos intents
        nuevos_intents = [
            # --- FLOTA: LISTADO ACTIVOS ---
            {
                'texto': "listado de móviles activos",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "qué móviles están reportando hoy",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "últimos reportes de los móviles",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "móviles funcionando ahora",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "ver móviles conectados",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "moviles activos",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "listado",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "lista",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "donde estan los moviles",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },
            {
                'texto': "cuales estan activos",
                'categoria': 'comando',
                'tipo': 'LISTADO_ACTIVOS',
                'accion': 'Listar móviles con reporte en últimas 24hs',
                'variables': {}
            },

            # --- FLOTA: SITUACIÓN ---
            {
                'texto': "situación general de la flota",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },
            {
                'texto': "estado de los móviles",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },
            {
                'texto': "qué móviles están circulando",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },
            {
                'texto': "cuáles están detenidos",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },
            {
                'texto': "resumen de la flota",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },
            {
                'texto': "como esta la flota",
                'categoria': 'comando',
                'tipo': 'SITUACION_FLOTA',
                'accion': 'Resumen de estado (circulando/detenido) y ubicación',
                'variables': {}
            },

            # --- ZONAS: MÓVILES EN ZONA ---
            {
                'texto': "móviles en zona Palermo",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "vehículos dentro de la zona Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "moviles en zona CABA",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "moviles en zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quien esta en zona Norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "listar móviles de la zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "qué está dentro del perímetro",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {}
            },
            {
                'texto': "ver móviles en área específica",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {}
            },
            {
                'texto': "quien esta en la zona norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_EN_ZONA',
                'accion': 'Listar móviles dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },

            # --- AYUDA ---
            {
                'texto': "ayuda",
                'categoria': 'ayuda',
                'tipo': 'AYUDA_GENERAL',
                'accion': 'Mostrar ayuda de comandos disponibles',
                'variables': {}
            },
            {
                'texto': "que puedes hacer",
                'categoria': 'ayuda',
                'tipo': 'AYUDA_GENERAL',
                'accion': 'Mostrar ayuda de comandos disponibles',
                'variables': {}
            },
            {
                'texto': "lista de comandos",
                'categoria': 'ayuda',
                'tipo': 'AYUDA_GENERAL',
                'accion': 'Mostrar ayuda de comandos disponibles',
                'variables': {}
            },
            {
                'texto': "que sabes hacer",
                'categoria': 'ayuda',
                'tipo': 'AYUDA_GENERAL',
                'accion': 'Mostrar ayuda de comandos disponibles',
                'variables': {}
            },
            {
                'texto': "ayuda con comandos",
                'categoria': 'ayuda',
                'tipo': 'AYUDA_GENERAL',
                'accion': 'Mostrar ayuda de comandos disponibles',
                'variables': {}
            },

            # --- VER EN MAPA/GOOGLE MAPS ---
            {
                'texto': "mostrar en mapa",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "ver en mapa",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "mostrar en google maps",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "ver en google maps",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "abrir mapa",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "mostrar mapa",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "ver mapa",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "mostrar en google",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
            {
                'texto': "ver en google",
                'categoria': 'comando',
                'tipo': 'VER_MAPA',
                'accion': 'Abrir Google Maps con la posición del móvil o zona',
                'variables': {}
            },
        ]

        count = 0
        for item in nuevos_intents:
            # Calcular vector
            vector = vectorizador.vectorizar(item['texto'])
            
            # Crear o actualizar
            obj, created = VectorConsulta.objects.update_or_create(
                texto_original=item['texto'],
                defaults={
                    'categoria': item['categoria'],
                    'tipo_consulta': item['tipo'],
                    'vector_embedding': vector,
                    'accion_asociada': item['accion'],
                    'variables': item['variables'],
                    'activo': True,
                    'threshold': 0.85  # Threshold por defecto
                }
            )
            
            status = "Creado" if created else "Actualizado"
            self.stdout.write(f"✅ {status}: {item['texto']} -> {item['tipo']}")
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"¡Proceso finalizado! Se procesaron {count} intents."))
