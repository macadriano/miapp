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

            # --- ZONAS: MÓVILES FUERA DE ZONA ---
            {
                'texto': "móviles fuera de zona Palermo",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "vehículos fuera de la zona Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "moviles fuera de zona CABA",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "moviles afuera de zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quien no esta en zona Norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "móviles que no están en la zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quienes están fuera del depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {}
            },
            {
                'texto': "móviles fuera del almacén",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {}
            },
            {
                'texto': "moviles no estan en la zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "moviles no están en la zona Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "no estan en zona Norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "no están en zona Sur",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuales estan fuera de zona Palermo",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuales están fuera de zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "Fuera de zona Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "fuera de zona Almacén",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "No estan en Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "no están en Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "cuales salieron de Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "cuales salieron de zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "móviles que salieron de Almacén",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "vehículos que salieron de zona Norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quienes salieron de Depósito 3",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "quien salio de zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quien salió de Almacén",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "móviles que no están en Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "vehículos que no están en zona Norte",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "quienes no están en Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "quien no esta en zona Sur",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "listar móviles fuera de Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "listar vehículos fuera de zona Almacén",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "móviles ausentes de zona Centro",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "vehículos ausentes de Depósito",
                'categoria': 'comando',
                'tipo': 'MOVILES_FUERA_DE_ZONA',
                'accion': 'Listar móviles que NO están dentro de una zona específica',
                'variables': {'zona': r'(.+)'}
            },

            # --- ZONAS: INGRESO A ZONA ---
            {
                'texto': "cuando ingreso ASN773 a zona Depósito",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "ingreso de MHW545 a zona CABA",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando entro el camion2 a zona Centro",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'movil': r'([a-zA-Z0-9]+)', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando ingresó OVV799 a zona Norte",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "ingreso a zona Depósito",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando entro a zona Almacén",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando ingresó a zona Centro",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "entrada a zona CABA",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando entro el vehiculo a zona Depósito",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando ingresó el movil a zona Norte",
                'categoria': 'pasado',
                'tipo': 'INGRESO_A_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil ingresó a una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },

            # --- ZONAS: SALIDA DE ZONA ---
            {
                'texto': "cuando salio ASN773 de zona Depósito",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "salida de MHW545 de zona CABA",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salio el camion2 de zona Centro",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'movil': r'([a-zA-Z0-9]+)', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salió OVV799 de zona Norte",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "salio de zona Depósito",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salio de zona Almacén",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salió de zona Centro",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "salida de zona CABA",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salio el vehiculo de zona Depósito",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando salió el movil de zona Norte",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "se salio de zona Depósito",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "se salió de zona Centro",
                'categoria': 'pasado',
                'tipo': 'SALIO_DE_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil salió de una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },

            # --- ZONAS: PASO POR ZONA ---
            {
                'texto': "cuando paso ASN773 por zona Depósito",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "paso de MHW545 por zona CABA",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando paso el camion2 por zona Centro",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'movil': r'([a-zA-Z0-9]+)', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando pasó OVV799 por zona Norte",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'movil': r'([A-Z0-9]{3,10})', 'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "paso por zona Depósito",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando paso por zona Almacén",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando pasó por zona Centro",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "paso por zona CABA",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando paso el vehiculo por zona Depósito",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "cuando pasó el movil por zona Norte",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "estuvo en zona Depósito",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "estuvo en zona Centro",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'zona\s+(.+)'}
            },
            {
                'texto': "estuvo en el deposito",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'(.+)'}
            },
            {
                'texto': "estuvo en el almacen",
                'categoria': 'pasado',
                'tipo': 'PASO_POR_ZONA',
                'accion': 'Buscar en histórico (últimos 2 días) cuándo un móvil pasó por una zona',
                'variables': {'zona': r'(.+)'}
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
