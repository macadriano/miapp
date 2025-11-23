"""
Comando para cargar vectores de ejemplo en la base de datos
"""
from django.core.management.base import BaseCommand
from agenteIA.models import VectorConsulta
import random

# Función para generar embeddings placeholder sin numpy
def generar_placeholder(texto):
    """Genera un embedding placeholder de 384 dimensiones"""
    random.seed(hash(texto) % 2**32)
    return [random.random() for _ in range(384)]
    
# Función para generar embedding aleatorio
def generar_random_embedding():
    """Genera un embedding completamente aleatorio"""
    return [random.random() for _ in range(384)]


class Command(BaseCommand):
    help = 'Carga vectores de ejemplo para Sofia'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Cargando vectores de ejemplo...'))
        
        # Función helper para generar embeddings consistentes
        def get_embedding(texto):
            return generar_placeholder(texto)
        
        # Vectores de ejemplo
        vectores_ejemplo = [
            # CATEGORÍA: ACTUAL
            {
                'texto_original': 'donde esta el camion XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_placeholder('donde esta el camion XXX'),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,  # Threshold más bajo para embeddings placeholder
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'El móvil {movil} se encuentra en {direccion}. Velocidad: {velocidad} km/h'
            },
            {
                'texto_original': 'cual es la ubicacion del vehiculo XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Ubicación del móvil {movil}: {direccion}'
            },
            {
                'texto_original': 'posicion del movil XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'El móvil {movil} está en {direccion}'
            },
            {
                'texto_original': 'donde esta XXX ahora',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': '{movil} está en {direccion}'
            },
            {
                'texto_original': 'donde anda el movil XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'El móvil {movil} está en {direccion}'
            },
            {
                'texto_original': 'por donde anda el movil XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'El móvil {movil} está en {direccion}'
            },
            {
                'texto_original': 'donde anda XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': '{movil} está en {direccion}'
            },
            {
                'texto_original': 'por donde anda XXX',
                'categoria': 'actual',
                'tipo_consulta': 'POSICION',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar posición actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': '{movil} está en {direccion}'
            },
            
            # CATEGORÍA: PASADO
            {
                'texto_original': 'donde estuvo ayer el camion XXX',
                'categoria': 'pasado',
                'tipo_consulta': 'RECORRIDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar recorrido de ayer del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Ayer el móvil {movil} recorrió {distancia} km, estuvo en {zonas} zonas'
            },
            {
                'texto_original': 'que hizo ayer el movil XXX',
                'categoria': 'pasado',
                'tipo_consulta': 'RECORRIDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar actividad de ayer del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'El móvil {movil} ayer: Distancia {distancia} km, Vel. máx {vel_max} km/h'
            },
            {
                'texto_original': 'recorrido del vehiculo XXX',
                'categoria': 'pasado',
                'tipo_consulta': 'RECORRIDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Consultar recorrido reciente del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Recorrido del móvil {movil}: {resumen}'
            },
            
            # CATEGORÍA: FUTURO
            {
                'texto_original': 'a que hora llega el MOVIL XXX a YYY',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX al lugar YYY',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b', 'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'El móvil {movil} llegará a {destino} aproximadamente en {tiempo}'
            },
            {
                'texto_original': 'cuanto tarda en llegar a YYY el MOVIL XXX',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX al lugar YYY',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b', 'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'El móvil {movil} llegará a {destino} aproximadamente en {tiempo}'
            },
            {
                'texto_original': 'cuanto demora en llegar a YYY el MOVIL XXX',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX al lugar YYY',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b', 'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'El móvil {movil} llegará a {destino} aproximadamente en {tiempo}'
            },
            {
                'texto_original': 'cuando llegaria a YYY el MOVIL XXX',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX al lugar YYY',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b', 'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'El móvil {movil} llegará a {destino} aproximadamente en {tiempo}'
            },
            {
                'texto_original': 'en cuanto llegaria a YYY el MOVIL XXX',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX al lugar YYY',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b', 'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'El móvil {movil} llegará a {destino} aproximadamente en {tiempo}'
            },
            {
                'texto_original': 'tiempo estimado de llegada del camion XXX',
                'categoria': 'futuro',
                'tipo_consulta': 'LLEGADA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Calcular tiempo estimado de llegada del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Tiempo estimado de {movil}: {tiempo}'
            },
            
            # CATEGORÍA: CERCANÍA
            {
                'texto_original': 'que movil esta mas cerca de YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que movil esta mas cerca de YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que vehiculo esta mas cerca de YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que vehiculo esta mas cerca de YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que camion esta mas cerca de YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que camion esta mas cerca de YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que movil esta mas cercano a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que movil esta mas cercano a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'cual es el movil mas cercano a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('cual es el movil mas cercano a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que movil esta mas cerca del movil XXX',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que movil esta mas cerca del movil XXX'),
                'accion_asociada': 'Encontrar móviles más cercanos al móvil XXX',
                'threshold': 0.3,
                'variables': {'movil_referencia': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Los móviles más cercanos a {movil_referencia} son: {resultado}'
            },
            {
                'texto_original': 'que vehiculo esta mas cerca del vehiculo XXX',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que vehiculo esta mas cerca del vehiculo XXX'),
                'accion_asociada': 'Encontrar móviles más cercanos al móvil XXX',
                'threshold': 0.3,
                'variables': {'movil_referencia': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Los móviles más cercanos a {movil_referencia} son: {resultado}'
            },
            {
                'texto_original': 'que movil esta mas proximo a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que movil esta mas proximo a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'cuales son los moviles mas cercanos a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('cuales son los moviles mas cercanos a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'cuales son los vehiculos mas cercanos a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('cuales son los vehiculos mas cercanos a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que vehiculos estan mas cerca de YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que vehiculos estan mas cercanos a YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que vehiculos estan mas cercanos a YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'cuales son los moviles mas cercanos YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('cuales son los moviles mas cercanos YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'cuales son los vehiculos mas cercanos YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('cuales son los vehiculos mas cercanos YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            {
                'texto_original': 'que moviles estan mas cercanos YYY',
                'categoria': 'cercania',
                'tipo_consulta': 'CERCANIA',
                'vector_embedding': get_embedding('que moviles estan mas cercanos YYY'),
                'accion_asociada': 'Encontrar móviles más cercanos a la ubicación YYY',
                'threshold': 0.3,
                'variables': {'destino': r'\b[A-Za-záéíóúñ\s\d]+\b'},
                'respuesta_template': 'Los móviles más cercanos a {destino} son: {resultado}'
            },
            
            # CATEGORÍA: COMANDO
            {
                'texto_original': 'enviame la ubicacion del vehiculo XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'comparte la posicion del movil XXX por whatsapp',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Compartir por WhatsApp la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Compartiendo ubicación de {movil}...'
            },
            
            # CATEGORÍA: SALUDO
            {
                'texto_original': 'hola sofia',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,  # Más flexible para saludos
                'variables': {},
                'respuesta_template': '¡Hola! Soy Sofia, tu asistente de GPS. ¿En qué puedo ayudarte?'
            },
            {
                'texto_original': 'buenos dias',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buenos días! ¿Cómo puedo ayudarte con tus vehículos hoy?'
            },
            {
                'texto_original': 'buenas tardes',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buenas tardes! Estoy aquí para ayudarte. ¿Qué necesitas?'
            },
            {
                'texto_original': 'buenas noches',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buenas noches! ¿En qué puedo ayudarte con tus vehículos?'
            },
            {
                'texto_original': 'hola',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hola! Soy Sofia. Puedo ayudarte a encontrar tus vehículos. ¿Qué necesitas?'
            },
            {
                'texto_original': 'hola que tal',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hola! Muy bien, gracias. ¿Qué puedo hacer por ti hoy?'
            },
            {
                'texto_original': 'buen dia',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buen día! ¿En qué puedo ayudarte?'
            },
            {
                'texto_original': 'buena tarde',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buena tarde! Estoy lista para ayudarte. ¿Qué necesitas?'
            },
            {
                'texto_original': 'hola buenas',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hola! Buenas, soy Sofia. ¿Cómo puedo ayudarte?'
            },
            {
                'texto_original': 'que tal sofia',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hola! Todo bien por acá. ¿Qué necesitas saber sobre tus vehículos?'
            },
            {
                'texto_original': 'hola como estas',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hola! Muy bien, gracias por preguntar. ¿En qué puedo ayudarte?'
            },
            {
                'texto_original': 'hey sofia',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Hey! Hola, soy Sofia. ¿Qué necesitas?'
            },
            {
                'texto_original': 'buen dia sofia',
                'categoria': 'saludo',
                'tipo_consulta': 'SALUDO',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Responder saludo',
                'threshold': 0.3,
                'variables': {},
                'respuesta_template': '¡Buen día! Estoy aquí para ayudarte. ¿Qué información necesitas?'
            },
            
            # CATEGORÍA: COMANDO - Enviar por WhatsApp (más variaciones)
            {
                'texto_original': 'mandame la ubicacion del vehiculo XXX por whatsapp',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'enviame por whatsapp donde esta XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación actual del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'compartime la posicion de XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Compartir la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Compartiendo ubicación de {movil}...'
            },
            {
                'texto_original': 'pasa la ubicacion del movil XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Compartir la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Compartiendo ubicación de {movil}...'
            },
            {
                'texto_original': 'quinta por whatsapp la posicion de XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'mandame por wsp donde esta el camion XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'necesito la ubicacion del vehiculo XXX en whatsapp',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
            {
                'texto_original': 'envia a whatsapp donde esta XXX',
                'categoria': 'comando',
                'tipo_consulta': 'COMANDO_WHATSAPP',
                'vector_embedding': generar_random_embedding(),
                'accion_asociada': 'Enviar por WhatsApp la ubicación del móvil XXX',
                'threshold': 0.3,
                'variables': {'movil': r'\b[A-Za-z0-9]{3,15}\b'},
                'respuesta_template': 'Enviando ubicación de {movil} por WhatsApp...'
            },
        ]
        
        # Eliminar vectores existentes
        VectorConsulta.objects.all().delete()
        self.stdout.write(self.style.WARNING('Vectores existentes eliminados'))
        
        # Cargar nuevos vectores
        for vector_data in vectores_ejemplo:
            VectorConsulta.objects.create(**vector_data)
            self.stdout.write(f"✓ Cargado: {vector_data['texto_original']}")
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Se cargaron {len(vectores_ejemplo)} vectores de ejemplo'))
        self.stdout.write(self.style.SUCCESS('Nota: Los embeddings son placeholders. Necesitas generar embeddings reales usando sentence-transformers'))

