from typing import Optional

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import VectorConsulta, ConversacionSofia
from .vectorizador import ProcesadorConsultas
from .matching_simple import ProcesadorSimple
from .acciones import EjecutorAcciones
from moviles.models import Movil
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
SESSION_ZONA_TIMEOUT_SECONDS = 300


def _guardar_zona_en_session(session, nombre_zona: str):
    """Guarda el nombre de la última zona consultada en la sesión."""
    if not nombre_zona:
        return
    session['ultima_zona_nombre'] = nombre_zona
    session['ultima_zona_timestamp'] = timezone.now().isoformat()
    session.modified = True


def _obtener_zona_de_session(session) -> Optional[str]:
    """Obtiene la última zona consultada desde la sesión si todavía es válida."""
    nombre = session.get('ultima_zona_nombre')
    timestamp_iso = session.get('ultima_zona_timestamp')

    if not nombre or not timestamp_iso:
        return None

    try:
        timestamp = datetime.fromisoformat(timestamp_iso)
        if timezone.is_naive(timestamp):
            timestamp = timezone.make_aware(timestamp, timezone.get_current_timezone())
    except Exception:
        return None

    if timezone.now() - timestamp > timedelta(seconds=SESSION_ZONA_TIMEOUT_SECONDS):
        return None

    return nombre
import json
import re


def _obtener_contexto_conversacion(usuario=None, ultimas_n=10):
    """
    Obtiene el contexto completo de la conversación reciente del usuario.
    Retorna un diccionario con información contextual rica.
    """
    try:
        desde = timezone.now() - timedelta(hours=2)
        # Optimizar consulta de conversaciones - solo campos necesarios
        conversaciones = ConversacionSofia.objects.filter(
            created_at__gte=desde
        ).only('id', 'datos_consulta', 'vector_usado', 'created_at', 'usuario')
        
        if usuario:
            conversaciones = conversaciones.filter(usuario=usuario)
        
        conversaciones = conversaciones.select_related('vector_usado', 'usuario').order_by('-created_at')[:ultimas_n]
        
        contexto = {
            'ultimo_movil': None,
            'ultimo_tipo_consulta': None,
            'ultimo_destino': None,
            'ultima_fecha': None,
            'historial_moviles': [],
            'historial_destinos': [],
            'historial_tipos': []
        }
        
        for conv in conversaciones:
            datos = conv.datos_consulta or {}
            tipo_consulta = None
            
            # Obtener tipo de consulta
            if conv.vector_usado:
                tipo_consulta = conv.vector_usado.tipo_consulta
            elif datos.get('tipo_consulta'):
                tipo_consulta = datos.get('tipo_consulta')
            
            # Obtener móvil
            movil = (datos.get('movil') or '').strip()
            if movil and movil.lower() not in ['donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con']:
                # SIEMPRE actualizar el último móvil si hay uno en la consulta (no solo si está vacío)
                contexto['ultimo_movil'] = movil
                if movil not in contexto['historial_moviles']:
                    contexto['historial_moviles'].append(movil)
            
            # Obtener destino (para LLEGADA)
            destino = (datos.get('destino') or '').strip()
            if destino:
                # Solo actualizar último destino si la consulta es LLEGADA o CERCANIA
                # No actualizar si es POSICION (para no sobrescribir con destinos antiguos)
                if tipo_consulta in ['LLEGADA', 'CERCANIA']:
                    contexto['ultimo_destino'] = destino
                elif not contexto['ultimo_destino']:
                    # Solo guardar si no hay uno previo (para no perder contexto de zonas)
                    contexto['ultimo_destino'] = destino
                if destino not in contexto['historial_destinos']:
                    contexto['historial_destinos'].append(destino)
            
            # Obtener zona (para UBICACION_ZONA)
            zona = (datos.get('zona') or '').strip()
            # También verificar si el destino es en realidad una zona
            if not zona and tipo_consulta == 'UBICACION_ZONA':
                # Si el tipo es UBICACION_ZONA pero no hay 'zona' en datos, intentar obtenerlo del destino
                zona = (datos.get('destino') or '').strip()
            if zona:
                # Guardar zona como destino para futuras consultas de CERCANIA/LLEGADA
                contexto['ultimo_destino'] = zona  # Siempre actualizar, no solo si está vacío
                if zona not in contexto['historial_destinos']:
                    contexto['historial_destinos'].append(zona)
                print(f"📍 Contexto: Guardando zona '{zona}' como último destino (tipo: {tipo_consulta})")
            
            # Guardar tipo de consulta - SIEMPRE actualizar (no solo si está vacío)
            if tipo_consulta:
                contexto['ultimo_tipo_consulta'] = tipo_consulta  # Siempre actualizar
                if tipo_consulta not in contexto['historial_tipos']:
                    contexto['historial_tipos'].append(tipo_consulta)
            
            # Guardar fecha de última consulta
            if not contexto['ultima_fecha']:
                contexto['ultima_fecha'] = conv.created_at
        
        return contexto
    except Exception as e:
        print(f"⚠️ Error obteniendo contexto de conversación: {e}")
        return {
            'ultimo_movil': None,
            'ultimo_tipo_consulta': None,
            'ultimo_destino': None,
            'ultima_fecha': None,
            'historial_moviles': [],
            'historial_destinos': [],
            'historial_tipos': []
        }


def _obtener_ultima_consulta_llegada(usuario=None):
    """
    Obtiene la última consulta de tipo LLEGADA del usuario.
    Retorna el tipo de consulta y el móvil usado si existe.
    """
    contexto = _obtener_contexto_conversacion(usuario, ultimas_n=5)
    
    if contexto['ultimo_tipo_consulta'] == 'LLEGADA':
        return True, contexto['ultimo_movil']
    
    return False, None


def _obtener_ultimo_movil_contexto(usuario=None):
    """
    Obtiene el último móvil consultado del historial de conversaciones del usuario.
    Busca en las últimas conversaciones (últimas 10) para encontrar un móvil exitosamente consultado.
    """
    try:
        # Buscar conversaciones recientes (últimas 2 horas o últimas 10 conversaciones)
        desde = timezone.now() - timedelta(hours=2)
        
        # Filtro por usuario si está autenticado, si no buscar todas
        conversaciones = ConversacionSofia.objects.filter(
            created_at__gte=desde
        )
        
        if usuario:
            conversaciones = conversaciones.filter(usuario=usuario)
        
        # Ordenar por fecha descendente y tomar las últimas 10
        conversaciones = conversaciones.order_by('-created_at')[:10]
        
        # Buscar en cada conversación si hay datos_consulta con móvil
        for conv in conversaciones:
            datos = conv.datos_consulta or {}
            
            # Intentar obtener móvil de varias formas:
            # 1. Variable 'movil' directa
            movil = datos.get('movil', '')
            if movil and movil.strip() and movil.lower() not in ['donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con']:
                return movil.strip()
            
            # 2. De datos_consulta si tiene información de móvil consultado
            # Buscar en el mensaje anterior si contenía un móvil
            mensaje_anterior = conv.mensaje_usuario or ''
            if mensaje_anterior:
                # Intentar extraer patente o nombre del mensaje anterior
                import unicodedata
                
                # Normalizar texto
                texto_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', mensaje_anterior)
                    if unicodedata.category(c) != 'Mn'
                )
                
                # Buscar patente
                patron_patente = r'\b([A-Z]{2,4})\s*(\d{2,4})\b'
                match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_encontrado = (match.group(1) + match.group(2)).upper()
                    return movil_encontrado
                
                # Buscar nombre alfanumérico
                patron_nombre = r'\b([a-zA-Z]+)\s*(\d+)\b'
                match = re.search(patron_nombre, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_encontrado = (match.group(1) + match.group(2)).lower()
                    return movil_encontrado
        
        return None
    except Exception as e:
        print(f"⚠️ Error obteniendo contexto de móvil: {e}")
        return None

# Vista para la interfaz principal de Sofia
def sofia_frontend(request):
    """Vista principal de la interfaz de Sofia"""
    # TODO: Reactivar autenticación en producción
    # @login_required
    return render(request, 'agenteIA/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def procesar_consulta(request):
    """
    Endpoint para procesar consultas de voz/texto de Sofia
    """
    import time
    start_time = time.time()
    
    # Logging inmediato para verificar que la petición llega
    print(f"\n{'='*80}")
    print(f"📥 [PROCESAR_CONSULTA] Petición recibida - Método: {request.method}")
    print(f"📥 [PROCESAR_CONSULTA] Path: {request.path}")
    print(f"📥 [PROCESAR_CONSULTA] Content-Type: {request.content_type}")
    print(f"{'='*80}\n")
    
    # TODO: Reactivar autenticación en producción
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        print(f"📥 [INICIO] Recibida petición")
        try:
            body_str = request.body.decode('utf-8')
            print(f"📥 [INICIO] Body (primeros 200 chars): {body_str[:200]}")
            data = json.loads(request.body)
            mensaje = data.get('mensaje', '')
            modo = data.get('modo', 'texto')  # 'texto' o 'voz'
            print(f"📝 [INICIO] Mensaje recibido: '{mensaje}' | Modo: {modo}")
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            return JsonResponse({
                'success': False,
                'respuesta': f"Error en el formato de la petición: {str(e)}",
                'respuesta_audio': "Error en el formato de la petición.",
                'error': str(e),
                'tiempo_procesamiento': round(time.time() - start_time, 2)
            }, status=400)
        except Exception as e:
            print(f"❌ Error procesando petición: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'respuesta': f"Error procesando petición: {str(e)}",
                'respuesta_audio': "Error procesando petición.",
                'error': str(e),
                'tiempo_procesamiento': round(time.time() - start_time, 2)
            }, status=400)
        
        # WORKAROUND: El frontend a veces agrega el móvil anterior al inicio del mensaje
        # Ejemplo: "CAMION2 cuanto tarda el camion5..." → "cuanto tarda el camion5..."
        # Detectar y remover móvil al inicio si viene seguido de una consulta
        patron_movil_inicio = r'^([A-Z]+\d+)\s+(.+)$'
        match_limpieza = re.match(patron_movil_inicio, mensaje.strip())
        if match_limpieza:
            posible_movil = match_limpieza.group(1)
            resto_mensaje = match_limpieza.group(2)
            # Solo limpiar si el resto del mensaje tiene palabras de consulta
            palabras_consulta = ['donde', 'cuanto', 'cuando', 'que', 'cual', 'como', 'llega', 'tarda', 'cerca']
            if any(palabra in resto_mensaje.lower() for palabra in palabras_consulta):
                print(f"⚠️ Limpiando mensaje: removiendo '{posible_movil}' del inicio")
                mensaje = resto_mensaje
        
        # Inicializar procesadores
        try:
            procesador = ProcesadorConsultas()
            procesador_simple = ProcesadorSimple()
            ejecutor = EjecutorAcciones()
            print(f"✅ Procesadores inicializados correctamente")
        except Exception as e:
            print(f"❌ Error inicializando procesadores: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'respuesta': f"Error al inicializar procesadores: {str(e)}",
                'respuesta_audio': "Ocurrió un error al inicializar el sistema.",
                'error': str(e),
                'tiempo_procesamiento': round(time.time() - start_time, 2)
            }, status=500)
        
        # Obtener todos los vectores activos - con cache
        try:
            cache_key = 'vectores_activos'
            vectores = cache.get(cache_key)
            if vectores is None:
                print(f"📊 Cargando vectores desde BD...")
                vectores = list(VectorConsulta.objects.filter(activo=True).only('id', 'texto_original', 'tipo_consulta', 'vector_embedding', 'activo', 'threshold', 'variables', 'categoria'))
                cache.set(cache_key, vectores, 300)  # Cache por 5 minutos
                print(f"✅ Cargados {len(vectores)} vectores desde BD")
            else:
                vectores = list(vectores)
                print(f"✅ Usando {len(vectores)} vectores desde cache")
        except Exception as e:
            print(f"❌ Error obteniendo vectores: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'respuesta': f"Error al obtener vectores: {str(e)}",
                'respuesta_audio': "Ocurrió un error al acceder a la base de datos.",
                'error': str(e),
                'tiempo_procesamiento': round(time.time() - start_time, 2)
            }, status=500)
        
        # Debug: verificar que hay vectores
        print(f"Consulta recibida: '{mensaje}'")
        print(f"Total vectores disponibles: {len(vectores)}")
        
        # Normalizar mensaje para comparaciones
        mensaje_lower = mensaje.lower().strip()
        
        # Detectar saludos y despedidas
        saludos = ['hola', 'hey', 'hi', 'buenos días', 'buenos dias', 'buenas tardes', 'buenas noches', 
                   'buen día', 'buen dia', 'buena tarde', 'buena noche', 'saludos', 'qué tal', 'que tal']
        despedidas = ['chau', 'chao', 'adiós', 'adios', 'hasta luego', 'hasta pronto', 'nos vemos', 
                     'hasta la vista', 'bye', 'bye bye', 'hasta mañana', 'hasta después', 'hasta despues',
                     'nos hablamos', 'nos vemos después', 'nos vemos despues', 'hasta la próxima', 'hasta la proxima']
        
        # Verificar si es un saludo puro (sin consulta adicional)
        # Un saludo puro es cuando solo contiene saludos y no tiene palabras clave de consultas
        palabras_consulta = [
            'donde', 'ubicacion', 'ubicación', 'posicion', 'posición', 'movil', 'móvil', 
            'vehiculo', 'vehículo', 'patente', 'flota', 'recorrido', 'historial', 
            'llegada', 'tiempo', 'velocidad', 'estado', 'informacion', 'información',
            'cuanto', 'cuánto', 'cuando', 'cuándo', 'tardaria', 'tardaría', 'tarda', 'demora', 'demoraria', 'demoraría',
            'llegar', 'llega', 'llegara', 'llegará', 'cerca', 'cercania', 'cercanía', 'proximo', 'próximo',
            'distancia', 'estimacion', 'estimación', 'hora', 'que', 'qué', 'cual', 'cuál'
        ]
        tiene_palabra_consulta = any(palabra in mensaje_lower for palabra in palabras_consulta)
        
        # Es saludo puro si tiene saludo, no tiene palabras de consulta, y tiene máximo 5 palabras
        es_saludo_puro = (any(saludo in mensaje_lower for saludo in saludos) and 
                         not tiene_palabra_consulta and 
                         len(mensaje_lower.split()) <= 5)
        
        # Verificar si es una despedida
        es_despedida = any(despedida in mensaje_lower for despedida in despedidas)
        
        # Responder a saludos puros
        if es_saludo_puro:
            saludos_respuesta = [
                "¡Hola! 👋 Soy Sofia, tu asistente de WayGPS. ¿En qué puedo ayudarte hoy?",
                "¡Hola! 😊 Estoy aquí para ayudarte con información sobre tu flota. ¿Qué necesitas?",
                "¡Hola! 👋 ¿Cómo puedo asistirte con el seguimiento de tus vehículos?",
                "¡Buenos días! ☀️ Soy Sofia. ¿En qué puedo ayudarte con tu flota?",
                "¡Buenas tardes! 🌅 Hola, soy Sofia. ¿Qué información necesitas?",
                "¡Buenas noches! 🌙 Soy Sofia, tu asistente. ¿En qué puedo ayudarte?"
            ]
            import random
            respuesta_saludo = random.choice(saludos_respuesta)
            
            return JsonResponse({
                'success': True,
                'respuesta': respuesta_saludo,
                'respuesta_audio': respuesta_saludo,
                'es_saludo': True
            })
        
        # Responder a despedidas
        if es_despedida:
            despedidas_respuesta = [
                "¡Hasta luego! 👋 Fue un placer ayudarte. ¡Que tengas un buen día!",
                "¡Chau! 😊 Cualquier cosa que necesites, aquí estaré. ¡Que estés bien!",
                "¡Hasta pronto! 👋 Estoy aquí cuando me necesites. ¡Cuídate!",
                "¡Adiós! 😊 Fue un gusto ayudarte. ¡Que tengas un excelente día!",
                "¡Nos vemos! 👋 Cualquier consulta, no dudes en preguntarme. ¡Hasta luego!",
                "¡Hasta la próxima! 😊 Fue un placer asistirte. ¡Que todo salga bien!"
            ]
            import random
            respuesta_despedida = random.choice(despedidas_respuesta)
            
            return JsonResponse({
                'success': True,
                'respuesta': respuesta_despedida,
                'respuesta_audio': respuesta_despedida,
                'es_despedida': True
            })
        
        # SISTEMA HÍBRIDO: Primero intentar matching por patrones (preciso)
        resultado = procesador_simple.procesar_consulta(mensaje, vectores)
        print(f"🔍 Matching por patrones: {'✅ Match' if resultado else '❌ No match'}")
        
        # Si no matchea con patrones, intentar sin saludo inicial
        if not resultado:
            # Detectar y remover saludos comunes del inicio
            patrones_saludo = [
                r'^(hola|hey|buenos?\s*dias?|buenas?\s*tardes|buenas?\s*noches)[,\s\.!]*\s*(.+)',
                r'^(hola\s+sofia|hey\s+sofia)[,\s\.!]*\s*(.+)',
            ]
            
            mensaje_sin_saludo = mensaje
            for patron in patrones_saludo:
                match = re.match(patron, mensaje_lower, re.IGNORECASE)
                if match:
                    last_group_index = match.lastindex or 0
                    consulta_despues = match.group(last_group_index).strip() if last_group_index else ''
                    if consulta_despues and len(consulta_despues) > 3:
                        mensaje_sin_saludo = consulta_despues
                        print(f"Mensaje original tiene saludo, procesando sin él: '{mensaje_sin_saludo}'")
                        break
            
            if mensaje_sin_saludo != mensaje and len(mensaje_sin_saludo) > 5:
                resultado = procesador_simple.procesar_consulta(mensaje_sin_saludo, vectores)
                print(f"🔍 Matching por patrones (sin saludo): {'✅ Match' if resultado else '❌ No match'}")
        
        # FALLBACK: Si patrones no funcionan, usar vectorización (más flexible pero menos preciso)
        if not resultado:
            print("🔍 Intentando con vectorización (fallback)...")
            resultado = procesador.procesar_consulta(mensaje, vectores)
            if resultado:
                print(f"✅ Match por vectorización: tipo={resultado.get('tipo')}, similitud={resultado.get('similitud', 0):.2f}")
                # Solo aceptar si la similitud es razonablemente alta (> 0.6)
                if resultado.get('similitud', 0) < 0.6:
                    print(f"⚠️ Similitud muy baja ({resultado.get('similitud', 0):.2f}), descartando match")
                    resultado = None
        
        # Obtener usuario para contexto (una sola vez, antes de cualquier procesamiento)
        usuario = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            usuario = request.user
        
        # Obtener contexto completo de la conversación (ANTES del matcher simple)
        contexto = _obtener_contexto_conversacion(usuario, ultimas_n=10)

        # Incorporar contexto guardado en la sesión (para usuarios no autenticados)
        zona_session = _obtener_zona_de_session(request.session)
        if zona_session:
            contexto['zona_session'] = zona_session
        
        # Variables auxiliares para manejo de contexto de zonas
        zona_contextual_usada = None
        zona_disponible = contexto.get('ultimo_destino')
        origen_zona_disponible = 'contexto' if zona_disponible else None
        if not zona_disponible and contexto.get('zona_session'):
            zona_disponible = contexto.get('zona_session')
            origen_zona_disponible = 'session'

        # PRIORIDAD 0.5: Si no hay contexto previo y el mensaje parece ser solo un nombre de móvil,
        # asumir que es una consulta de POSICION (evitar interpretarlo como destino)
        if not contexto['ultimo_tipo_consulta'] and not resultado:
            # Intentar extraer un móvil del mensaje
            movil_detectado = procesador_simple.matcher.extraer_movil(mensaje)
            tokens = mensaje.strip().split()
            
            # Si se detectó un móvil y el mensaje es corto (sin palabras de pregunta/comando)
            palabras_pregunta_comando = ['donde', 'cuando', 'cuanto', 'que', 'como', 'cual', 'quien', 
                                         'por que', 'porque', 'whatsapp', 'wsp', 'enviar', 'compartir', 
                                         'mandar', 'enviame', 'mandame', 'llega', 'llegar', 'tarda', 'demora']
            tiene_palabra_pregunta_comando = any(palabra in mensaje_lower for palabra in palabras_pregunta_comando)
            
            if movil_detectado and len(tokens) <= 4 and not tiene_palabra_pregunta_comando:
                print(f"📍 [PRIORIDAD 0.5] Sin contexto previo, detectado móvil '{movil_detectado}' - asumiendo POSICION")
                # Buscar un vector de POSICION
                for vector_db in vectores:
                    if vector_db.tipo_consulta == 'POSICION' and vector_db.activo:
                        resultado = {
                            'tipo': 'POSICION',
                            'similitud': 0.85,
                            'variables': {
                                'movil': movil_detectado
                            },
                            'vector': vector_db
                        }
                        print(f"✅ [PRIORIDAD 0.5] Forzando tipo POSICION con móvil: '{movil_detectado}'")
                        break
        
        # PRIORIDAD 0: Detectar continuaciones de consultas basadas en contexto
        # Esto debe ejecutarse ANTES del matcher simple para evitar interpretaciones incorrectas
        # Si la última consulta fue LLEGADA y el mensaje actual parece ser solo un destino
        if contexto['ultimo_tipo_consulta'] == 'LLEGADA' and not resultado:
            # PRIMERO: Verificar si es una frase común (no procesar como destino)
            frases_comunes_continuacion = [
                'ok', 'okay', 'okey', 'okey dokey',
                'gracias', 'muchas gracias', 'muchísimas gracias', 'gracias a vos', 'gracias a ti',
                'de nada', 'no hay de qué', 'por nada', 'a vos', 'a ti',
                'perfecto', 'perfecto gracias', 'perfecto, gracias',
                'genial', 'genial gracias', 'genial, gracias',
                'excelente', 'excelente gracias', 'excelente, gracias',
                'bien', 'muy bien', 'está bien', 'esta bien',
                'entendido', 'entendido gracias', 'entendido, gracias',
                'listo', 'listo gracias', 'listo, gracias',
                'dale', 'dale gracias', 'dale, gracias',
                'bueno', 'bueno gracias', 'bueno, gracias',
                'vale', 'vale gracias', 'vale, gracias',
                'si', 'sí', 'si gracias', 'sí gracias', 'si, gracias', 'sí, gracias',
                'claro', 'claro gracias', 'claro, gracias',
                'por supuesto', 'por supuesto gracias', 'por supuesto, gracias',
                'de acuerdo', 'de acuerdo gracias', 'de acuerdo, gracias',
                'bárbaro', 'barbaro', 'bárbaro gracias', 'barbaro gracias',
                'joya', 'joya gracias', 'joya, gracias',
                'buenísimo', 'buenisimo', 'buenísimo gracias', 'buenisimo gracias',
            ]
            
            es_frase_comun_continuacion = (any(frase in mensaje_lower for frase in frases_comunes_continuacion) and 
                                          not tiene_palabra_consulta and 
                                          len(mensaje_lower.split()) <= 4)
            
            if es_frase_comun_continuacion:
                print(f"📍 [PRIORIDAD 0] Aunque hay contexto de LLEGADA, '{mensaje}' es una frase común - NO forzando LLEGADA")
                # No hacer nada, dejar que se procese normalmente (probablemente como frase común al final)
            
            # SEGUNDO: Verificar si el mensaje parece ser un móvil (no un destino)
            elif not es_frase_comun_continuacion:
                movil_detectado_en_continuacion = procesador_simple.matcher.extraer_movil(mensaje)
                tokens = mensaje.strip().split()
                palabras_pregunta_comando = ['donde', 'cuando', 'cuanto', 'que', 'como', 'cual', 'quien', 
                                             'por que', 'porque', 'whatsapp', 'wsp', 'enviar', 'compartir', 
                                             'mandar', 'enviame', 'mandame', 'llega', 'llegar', 'tarda', 'demora']
                tiene_palabra_pregunta_comando = any(palabra in mensaje_lower for palabra in palabras_pregunta_comando)
                
                print(f"🔍 [PRIORIDAD 0] Verificando si '{mensaje}' es un móvil: detectado={movil_detectado_en_continuacion}, tokens={len(tokens)}, tiene_palabra={tiene_palabra_pregunta_comando}")
                
                # Si parece ser un móvil, NO forzar LLEGADA (forzar POSICION en su lugar)
                if movil_detectado_en_continuacion and len(tokens) <= 4 and not tiene_palabra_pregunta_comando:
                    print(f"📍 [PRIORIDAD 0] Aunque hay contexto de LLEGADA, '{mensaje}' parece ser un móvil - forzando POSICION")
                    # Buscar un vector de POSICION
                    for vector_db in vectores:
                        if vector_db.tipo_consulta == 'POSICION' and vector_db.activo:
                            resultado = {
                                'tipo': 'POSICION',
                                'similitud': 0.85,
                                'variables': {
                                    'movil': movil_detectado_en_continuacion
                                },
                                'vector': vector_db
                            }
                            print(f"✅ [PRIORIDAD 0] Forzando tipo POSICION con móvil: '{movil_detectado_en_continuacion}'")
                            break
                else:
                    # Detectar referencias implícitas
                    referencias_movil = ['ese', 'este', 'el mismo', 'ese movil', 'este movil', 'el movil', 'ese camion', 'este camion']
                    referencias_destino = ['ese lugar', 'ese destino', 'ese sitio', 'allí', 'allá', 'ese']
                    
                    tiene_referencia_movil = any(ref in mensaje_lower for ref in referencias_movil)
                    tiene_referencia_destino = any(ref in mensaje_lower for ref in referencias_destino)
                    
                    # Verificar primero si es una consulta de CERCANIA sin destino específico
                    patrones_cercania_sin_destino = [
                        r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*[?.,!;:]*\s*$',
                        r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca\s*[?.,!;:]*\s*$',
                        r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*[?.,!;:]*\s*$',
                        r'^m[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*[?.,!;:]*\s*$',  # Patrón más flexible al inicio
                    ]
                    es_cercania_sin_destino = any(re.search(patron, mensaje_lower.strip(), re.IGNORECASE) for patron in patrones_cercania_sin_destino)
                    
                    # NUEVA LÓGICA: Si es CERCANIA sin destino, usar el contexto (zona o móvil)
                    # PRIORIDAD: Si la última consulta fue de un móvil (POSICION), usar ese móvil
                    # Si la última consulta fue de una zona (UBICACION_ZONA), usar esa zona
                    if es_cercania_sin_destino:
                        ultimo_tipo = contexto.get('ultimo_tipo_consulta', '')
                        ultimo_movil = (contexto.get('ultimo_movil') or '').strip()
                        ultimo_destino = (contexto.get('ultimo_destino') or '').strip()
                        
                        # PRIORIDAD 1: Si la última consulta fue POSICION (móvil), usar ese móvil
                        if ultimo_tipo == 'POSICION' and ultimo_movil:
                            print(f"📍 [PRIORIDAD 0] CERCANIA sin destino - última consulta fue POSICION, usando móvil: '{ultimo_movil}'")
                            resultado = {
                                'tipo': 'CERCANIA',
                                'similitud': 0.9,
                                'variables': {
                                    'movil_referencia': ultimo_movil,
                                },
                                'vector': None
                            }
                            print(f"✅ [PRIORIDAD 0] Forzando tipo CERCANIA con móvil del contexto: '{ultimo_movil}'")
                        # PRIORIDAD 2: Si la última consulta fue UBICACION_ZONA (zona), usar esa zona
                        elif ultimo_tipo == 'UBICACION_ZONA' and ultimo_destino:
                            print(f"📍 [PRIORIDAD 0] CERCANIA sin destino - última consulta fue UBICACION_ZONA, usando zona: '{ultimo_destino}'")
                            resultado = {
                                'tipo': 'CERCANIA',
                                'similitud': 0.9,
                                'variables': {
                                    'destino': ultimo_destino,
                                },
                                'vector': None
                            }
                            zona_contextual_usada = ultimo_destino
                            print(f"✅ [PRIORIDAD 0] Forzando tipo CERCANIA con zona del contexto: '{ultimo_destino}'")
                        # PRIORIDAD 3: Si hay móvil en contexto (aunque no sea la última consulta), usar ese móvil
                        elif ultimo_movil:
                            print(f"📍 [PRIORIDAD 0] CERCANIA sin destino - usando móvil del contexto: '{ultimo_movil}'")
                            resultado = {
                                'tipo': 'CERCANIA',
                                'similitud': 0.9,
                                'variables': {
                                    'movil_referencia': ultimo_movil,
                                },
                                'vector': None
                            }
                            print(f"✅ [PRIORIDAD 0] Forzando tipo CERCANIA con móvil del contexto: '{ultimo_movil}'")
                        # PRIORIDAD 4: Si hay zona en contexto (aunque no sea la última consulta), usar esa zona
                        elif ultimo_destino:
                            print(f"📍 [PRIORIDAD 0] CERCANIA sin destino - usando zona del contexto: '{ultimo_destino}'")
                            resultado = {
                                'tipo': 'CERCANIA',
                                'similitud': 0.9,
                                'variables': {
                                    'destino': ultimo_destino,
                                },
                                'vector': None
                            }
                            zona_contextual_usada = ultimo_destino
                            print(f"✅ [PRIORIDAD 0] Forzando tipo CERCANIA con zona del contexto: '{ultimo_destino}'")
                        else:
                            # Sin contexto - mostrar móviles más cercanos entre sí
                            print(f"📍 [PRIORIDAD 0] CERCANIA sin destino y sin contexto - mostrando móviles más cercanos entre sí")
                            resultado = {
                                'tipo': 'CERCANIA',
                                'similitud': 0.9,
                                'variables': {
                                    # Sin destino - mostrará móviles más cercanos entre sí
                                },
                                'vector': None
                            }
                            print(f"✅ [PRIORIDAD 0] Forzando tipo CERCANIA sin destino (móviles más cercanos entre sí)")
                    else:
                        palabras_pregunta = ['donde', 'cuando', 'cuanto', 'que', 'como', 'cual', 'cuales', 'cuáles', 'quien', 'por que', 'porque']
                        palabras_comando = ['whatsapp', 'wsp', 'enviar', 'compartir', 'mandar', 'enviame', 'mandame']
                        palabras_verbo = ['esta', 'está', 'estuvo', 'estaba', 'llega', 'llegó', 'llegara', 'tarda', 'demora', 'hace', 'hizo', 'son', 'están']
                        
                        tiene_palabra_pregunta = any(palabra in mensaje_lower for palabra in palabras_pregunta)
                        tiene_palabra_comando = any(palabra in mensaje_lower for palabra in palabras_comando)
                        tiene_verbo = any(palabra in mensaje_lower for palabra in palabras_verbo)
                        
                        # Si parece ser solo un nombre de lugar/destino (sin preguntas, comandos ni verbos)
                        if not tiene_palabra_pregunta and not tiene_palabra_comando and not tiene_verbo:
                            # Probablemente es solo un nombre de lugar/destino (puede ser una zona)
                            print(f"📍 [PRIORIDAD 0] Detectada continuación de LLEGADA: '{mensaje}' parece ser solo un destino")
                            resultado = {
                                'tipo': 'LLEGADA',
                                'similitud': 0.9,
                                'variables': {
                                    'destino': mensaje.strip(),
                                    'movil': contexto['ultimo_movil'] if contexto['ultimo_movil'] else ''
                                },
                                'vector': None
                            }
                            print(f"✅ [PRIORIDAD 0] Forzando tipo LLEGADA con destino: '{mensaje.strip()}' y móvil: '{contexto['ultimo_movil']}'")
                            # El usuario se agregará más adelante en el flujo (línea ~527)
                        elif tiene_referencia_destino and contexto['ultimo_destino']:
                            # Referencia implícita al último destino
                            print(f"📍 [PRIORIDAD 0] Detectada referencia implícita al último destino: '{contexto['ultimo_destino']}'")
                            resultado = {
                                'tipo': 'LLEGADA',
                                'similitud': 0.9,
                                'variables': {
                                    'destino': contexto['ultimo_destino'],
                                    'movil': contexto['ultimo_movil'] if contexto['ultimo_movil'] else ''
                                },
                                'vector': None
                            }
        
        # VERIFICACIÓN PRIORITARIA: Si hay contexto de zona y la consulta menciona explícitamente esa zona
        # IMPORTANTE: Solo se ejecuta si NO es "móviles más cercanos" sin destino (ese caso ya fue manejado en PRIORIDAD 0)
        if not resultado:
            # Verificar si es "móviles más cercanos" sin destino - si es así, NO usar zona del contexto aquí
            # (ya fue manejado en PRIORIDAD 0 con la lógica correcta de prioridad móvil/zona)
            patrones_cercania_sin_destino = [
                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',
                r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca\s*$',
                r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',
            ]
            es_cercania_sin_destino_verificacion = any(re.search(patron, mensaje_lower, re.IGNORECASE) for patron in patrones_cercania_sin_destino)
            
            # Si es "móviles más cercanos" sin destino, NO usar zona del contexto aquí
            # (debe usar la lógica de PRIORIDAD 0 que ya prioriza móvil sobre zona)
            if es_cercania_sin_destino_verificacion:
                print(f"ℹ️ [VERIFICACIÓN PRIORITARIA] Es 'móviles más cercanos' sin destino - NO usando zona del contexto (ya manejado en PRIORIDAD 0)")
            else:
                # Verificar si el mensaje menciona EXPLÍCITAMENTE la zona del contexto
                # O si menciona palabras como "allí", "ese lugar", "ese destino", etc.
                mensaje_normalizado = re.sub(r'\s+', ' ', mensaje_lower.strip())
                
                # Patrones que indican referencia explícita al destino del contexto
                referencias_explicitas = [
                    r'all[ií]',
                    r'all[aá]',
                    r'ese\s+(?:lugar|destino|sitio|punto)',
                    r'ese\s+(?:zona|deposito|almacen)',
                    r'a\s+(?:ese|aquel)\s+(?:lugar|destino|sitio)',
                    r'(?:m[oó]viles?\s+)?m[aá]s\s+cercan[oa]s?\s+(?:a|de|del|de\s+la)\s*(?:ese|aquel)',
                ]
                
                # Verificar si menciona la zona por nombre
                menciona_zona_por_nombre = zona_disponible and zona_disponible.lower() in mensaje_normalizado
                
                # Verificar si hay referencia explícita
                tiene_referencia_explicita = any(re.search(patron, mensaje_normalizado, re.IGNORECASE) for patron in referencias_explicitas)
                
                # Solo usar el destino del contexto si:
                # 1. Menciona la zona por nombre, O
                # 2. Tiene referencia explícita al destino del contexto
                if (menciona_zona_por_nombre or tiene_referencia_explicita) and zona_disponible:
                    print(f"🎯 [VERIFICACIÓN PRIORITARIA] Detectada referencia explícita a zona disponible: '{zona_disponible}'")
                    resultado = {
                        'tipo': 'CERCANIA',
                        'similitud': 0.95,
                        'variables': {
                            'destino': zona_disponible,
                        },
                        'vector': None
                    }
                    zona_contextual_usada = zona_disponible
                    print(f"✅ [VERIFICACIÓN PRIORITARIA] Forzando CERCANIA con zona disponible: '{zona_disponible}'")
        
        # Fallback: si no encontró resultado y la similitud máxima fue muy baja, usar matcher simple
        if not resultado:
            print("⚠️ No se encontró resultado con vectores, usando matcher simple...")
            resultado = procesador_simple.procesar_consulta(mensaje, vectores)
        
        # VERIFICACIÓN POST-SIMPLEMATCHER: Si SimpleMatcher detectó CERCANIA sin destino
        # NO usar automáticamente el destino del contexto - solo si el usuario lo menciona explícitamente
        if resultado and resultado.get('tipo') == 'CERCANIA':
            # Verificar si es una consulta sin destino específico (patrones más flexibles)
            mensaje_normalizado = re.sub(r'\s+', ' ', mensaje_lower.strip())
            patrones_cercania_sin_destino = [
                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',
                r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca\s*$',
                r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',
                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?',  # Sin $ para más flexibilidad
                r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca',  # Sin $ para más flexibilidad
                r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?',  # Sin $ para más flexibilidad
            ]
            es_cercania_sin_destino = any(re.search(patron, mensaje_normalizado, re.IGNORECASE) for patron in patrones_cercania_sin_destino)
            
            # Verificar si NO hay destino en variables
            variables_resultado = resultado.get('variables', {})
            tiene_destino_en_resultado = (variables_resultado.get('destino') or '').strip()
            
            # Si es CERCANIA sin destino, NO usar automáticamente la zona del contexto
            # Solo usar si el usuario menciona explícitamente la zona o hace referencia explícita
            if es_cercania_sin_destino and not tiene_destino_en_resultado:
                # Verificar si menciona la zona por nombre o tiene referencia explícita
                menciona_zona_por_nombre = zona_disponible and zona_disponible.lower() in mensaje_normalizado
                referencias_explicitas = [
                    r'all[ií]',
                    r'all[aá]',
                    r'ese\s+(?:lugar|destino|sitio|punto)',
                    r'ese\s+(?:zona|deposito|almacen)',
                    r'a\s+(?:ese|aquel)\s+(?:lugar|destino|sitio)',
                ]
                tiene_referencia_explicita = any(re.search(patron, mensaje_normalizado, re.IGNORECASE) for patron in referencias_explicitas)
                
                # Solo usar el destino del contexto si hay referencia explícita
                if (menciona_zona_por_nombre or tiene_referencia_explicita) and zona_disponible:
                    print(f"🎯 [POST-SIMPLEMATCHER] Detectada referencia explícita a zona disponible: '{zona_disponible}'")
                    if 'variables' not in resultado:
                        resultado['variables'] = {}
                    resultado['variables']['destino'] = zona_disponible
                    resultado['similitud'] = 0.95
                    zona_contextual_usada = zona_disponible
                    print(f"✅ [POST-SIMPLEMATCHER] Asignando zona disponible como destino: '{zona_disponible}'")
                else:
                    print(f"ℹ️ [POST-SIMPLEMATCHER] CERCANIA sin destino - NO usando zona del contexto automáticamente (mostrará móviles más cercanos entre sí)")
            elif tiene_destino_en_resultado:
                print(f"ℹ️ [POST-SIMPLEMATCHER] CERCANIA ya tiene destino en resultado: '{tiene_destino_en_resultado}'")
        
        # Corrección inteligente ANTES de procesar: detectar comandos y tiempos
        expresiones_pasado = ['hace', 'ayer', 'semana pasada', 'mes pasado', 'estaba', 'estuvo', 'donde estaba', 'donde estuvo']
        tiene_tiempo_pasado = any(exp in mensaje_lower for exp in expresiones_pasado)
        
        # PALABRAS CLAVE PARA COMANDOS
        palabras_whatsapp = ['whatsapp', 'wsp', 'enviame', 'mandame', 'compartime', 'pasa', 'comparte', 'envia']
        es_comando_whatsapp = any(palabra in mensaje_lower for palabra in palabras_whatsapp)
        
        # PRIORIDAD 1: Comandos de WhatsApp
        if es_comando_whatsapp and resultado:
            print("Detectado comando de WhatsApp, forzando tipo COMANDO_WHATSAPP")
            resultado['tipo'] = 'COMANDO_WHATSAPP'
            print(f"✅ Tipo corregido a COMANDO_WHATSAPP")
        
        # PRIORIDAD 2: Detectar continuaciones de consultas basadas en contexto (fallback)
        # Si la última consulta fue de un tipo específico y la actual parece ser una continuación
        if not resultado and contexto['ultimo_tipo_consulta']:
            # Detectar referencias implícitas
            referencias_movil = ['ese', 'este', 'el mismo', 'ese movil', 'este movil', 'el movil', 'ese camion', 'este camion']
            referencias_destino = ['ese lugar', 'ese destino', 'ese sitio', 'allí', 'allá', 'ese']
            
            tiene_referencia_movil = any(ref in mensaje_lower for ref in referencias_movil)
            tiene_referencia_destino = any(ref in mensaje_lower for ref in referencias_destino)
            
            palabras_pregunta = ['donde', 'cuando', 'cuanto', 'que', 'como', 'cual', 'quien', 'por que', 'porque']
            palabras_comando = ['whatsapp', 'wsp', 'enviar', 'compartir', 'mandar', 'enviame', 'mandame']
            palabras_verbo = ['esta', 'está', 'estuvo', 'estaba', 'llega', 'llegó', 'llegara', 'tarda', 'demora', 'hace', 'hizo']
            
            tiene_palabra_pregunta = any(palabra in mensaje_lower for palabra in palabras_pregunta)
            tiene_palabra_comando = any(palabra in mensaje_lower for palabra in palabras_comando)
            tiene_verbo = any(palabra in mensaje_lower for palabra in palabras_verbo)
            
            # Continuación de POSICION: si la última fue POSICION y hay referencia al móvil
            if contexto['ultimo_tipo_consulta'] == 'POSICION' and tiene_referencia_movil:
                if contexto['ultimo_movil']:
                    print(f"📍 Detectada referencia implícita al último móvil: '{contexto['ultimo_movil']}'")
                    resultado = {
                        'tipo': 'POSICION',
                        'similitud': 0.9,
                        'variables': {
                            'movil': contexto['ultimo_movil']
                        },
                        'vector': None
                    }
            
            # Si hay referencia a móvil pero no se especificó, usar el último
            elif tiene_referencia_movil and contexto['ultimo_movil'] and resultado:
                if not resultado.get('variables', {}).get('movil'):
                    resultado['variables']['movil'] = contexto['ultimo_movil']
                    resultado['variables']['_usando_contexto'] = True
                    print(f"📍 Usando móvil del contexto: '{contexto['ultimo_movil']}'")
        
        # PRIORIDAD 3: Detectar consultas de tiempo de arribo con "hasta" o "a [destino]"
        # Estas deben ser LLEGADA, no CERCANIA
        if resultado and mensaje_lower:
            patrones_arribo = [
                'cuanto tardaria hasta', 'cuanto demoraria hasta',
                'cuanto tarda hasta', 'cuanto demora hasta',
                'cuanto tardaria en llegar a', 'cuanto demoraria en llegar a',
                'cuanto tarda a ', 'cuanto tardaria a ',
                'cuanto demora a ', 'cuanto demoraria a ',
                'cuanto tiempo tarda a ', 'cuanto tiempo demora a '
            ]
            es_arribo = any(patron in mensaje_lower for patron in patrones_arribo)
            if es_arribo and resultado.get('tipo') != 'LLEGADA':
                print(f"⚠️ Detectado patrón de arribo, corrigiendo tipo a LLEGADA (era {resultado.get('tipo')})")
                resultado['tipo'] = 'LLEGADA'
                # Buscar un vector de LLEGADA si no lo tiene
                if not resultado.get('vector'):
                    for vector_db in vectores:
                        if vector_db.tipo_consulta == 'LLEGADA' and vector_db.activo:
                            resultado['vector'] = vector_db
                            break
        # PRIORIDAD 2: Preguntas históricas
        elif tiene_tiempo_pasado and resultado:
            print("Detectada pregunta histórica, forzando tipo RECORRIDO")
            resultado['tipo'] = 'RECORRIDO'
            print(f"✅ Tipo corregido a RECORRIDO")
        # PRIORIDAD 3: Preguntas en presente
        elif ('donde esta' in mensaje_lower or 'donde está' in mensaje_lower) and not tiene_tiempo_pasado:
            print("Detectada pregunta en presente sin tiempo pasado, forzando tipo POSICION")
            # Reescribir resultado si existe
            if resultado and resultado['tipo'] != 'POSICION':
                resultado['tipo'] = 'POSICION'
                print(f"✅ Tipo corregido a POSICION")
        
        print(f"Resultado del procesamiento: {resultado is not None}")
        if resultado:
            print(f"✅ Resultado encontrado - Tipo de consulta: {resultado.get('tipo', 'N/A')}")
            print(f"📊 Similitud: {resultado.get('similitud', 'N/A')}")
            print(f"📝 Variables extraídas: {resultado.get('variables', {})}")
        else:
            print(f"⚠️ No se encontró resultado para el mensaje: '{mensaje}'")
        
        if resultado:
            # Se encontró una coincidencia
            vector_usado = resultado.get('vector')
            similitud = resultado['similitud']
            variables = resultado.get('variables', {})
            historial_recorridos = []  # Inicializar lista vacía para historial
            
            # Obtener tipo ANTES de extraer móvil (importante para LLEGADA)
            tipo_consulta = resultado['tipo']
            
            # Pasar el texto completo para extracción de fallback
            variables['_texto_completo'] = mensaje
            
            # Guardar el tipo de consulta y contexto en variables para que se guarde en la conversación
            variables['tipo_consulta'] = tipo_consulta
            
            # Guardar información contextual adicional para futuras consultas
            if 'destino' in variables and variables['destino']:
                variables['_ultimo_destino'] = variables['destino']
            if 'zona' in variables and variables['zona']:
                # Guardar zona como destino para futuras consultas de CERCANIA/LLEGADA
                variables['_ultimo_destino'] = variables['zona']
                variables['destino'] = variables['zona']  # También guardar como destino
                # IMPORTANTE: Asegurar que la zona se guarde para el contexto
                print(f"📍 Guardando zona en variables: '{variables['zona']}' como destino")
            if 'movil' in variables and variables['movil']:
                variables['_ultimo_movil'] = variables['movil']
            
            # Guardar zona en sesión para futuras consultas contextuales
            if tipo_consulta == 'UBICACION_ZONA' and variables.get('destino'):
                _guardar_zona_en_session(request.session, variables['destino'])
            elif tipo_consulta == 'CERCANIA' and zona_contextual_usada:
                _guardar_zona_en_session(request.session, zona_contextual_usada)
            
            # VERIFICACIÓN ESPECIAL: Si es CERCANIA sin destino en variables pero hay contexto
            # (puede venir del SimpleMatcher sin pasar por PRIORIDAD 0)
            # IMPORTANTE: Respetar la prioridad: móvil sobre zona
            if tipo_consulta == 'CERCANIA' and not variables.get('destino') and not variables.get('destino_texto') and not variables.get('movil_referencia'):
                ultimo_tipo = contexto.get('ultimo_tipo_consulta', '')
                ultimo_movil = (contexto.get('ultimo_movil') or '').strip()
                ultimo_destino = (contexto.get('ultimo_destino') or '').strip()
                
                # PRIORIDAD 1: Si la última consulta fue POSICION (móvil), usar ese móvil
                if ultimo_tipo == 'POSICION' and ultimo_movil:
                    print(f"📍 [POST-MATCHING] CERCANIA sin destino, última consulta fue POSICION, usando móvil: '{ultimo_movil}'")
                    variables['movil_referencia'] = ultimo_movil
                    print(f"✅ [POST-MATCHING] Asignando móvil del contexto como referencia: '{ultimo_movil}'")
                # PRIORIDAD 2: Si la última consulta fue UBICACION_ZONA (zona), usar esa zona
                elif ultimo_tipo == 'UBICACION_ZONA' and ultimo_destino:
                    print(f"📍 [POST-MATCHING] CERCANIA sin destino, última consulta fue UBICACION_ZONA, usando zona: '{ultimo_destino}'")
                    variables['destino'] = ultimo_destino
                    print(f"✅ [POST-MATCHING] Asignando zona del contexto como destino: '{ultimo_destino}'")
                # PRIORIDAD 3: Si hay móvil en contexto (aunque no sea la última consulta), usar ese móvil
                elif ultimo_movil:
                    print(f"📍 [POST-MATCHING] CERCANIA sin destino, usando móvil del contexto: '{ultimo_movil}'")
                    variables['movil_referencia'] = ultimo_movil
                    print(f"✅ [POST-MATCHING] Asignando móvil del contexto como referencia: '{ultimo_movil}'")
                # PRIORIDAD 4: Si hay zona en contexto (aunque no sea la última consulta), usar esa zona
                elif ultimo_destino:
                    print(f"📍 [POST-MATCHING] CERCANIA sin destino, usando zona del contexto: '{ultimo_destino}'")
                    variables['destino'] = ultimo_destino
                    print(f"✅ [POST-MATCHING] Asignando zona del contexto como destino: '{ultimo_destino}'")
            
            # Si no hay móvil en variables pero hay en contexto, guardarlo para referencia
            # Esto es importante para VER_MAPA y CERCANIA que pueden usar el contexto
            if not variables.get('movil') and contexto.get('ultimo_movil'):
                variables['_contexto_movil_disponible'] = contexto['ultimo_movil']
                variables['movil_referencia'] = contexto['ultimo_movil']
                print(f"📍 Guardando móvil del contexto para referencia: '{contexto['ultimo_movil']}'")
            
            # Para VER_MAPA, SIEMPRE pasar el contexto del móvil si no hay móvil especificado
            if tipo_consulta == 'VER_MAPA' and not variables.get('movil') and contexto.get('ultimo_movil'):
                variables['_contexto_movil_disponible'] = contexto['ultimo_movil']
                variables['movil'] = contexto['ultimo_movil']  # También ponerlo en movil para que _ver_en_mapa lo use
                print(f"🗺️ [VER_MAPA] Usando móvil del contexto: '{contexto['ultimo_movil']}'")
            
            # Usuario ya obtenido arriba
            
            # VERIFICACIÓN PREVIA: Si hay palabra "zona" en el texto y es POSICION, verificar primero si es zona
            # Esto debe hacerse ANTES de extraer el móvil para evitar confundir zonas con móviles
            if tipo_consulta == 'POSICION':
                tiene_palabra_zona = re.search(r'\b(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\b', mensaje_lower, re.IGNORECASE)
                if tiene_palabra_zona:
                    # Intentar extraer nombre de zona
                    nombre_extraido = None
                    patrones_extraccion = [
                        # "zona depósito 3" o "la zona depósito 3"
                        r'(?:el|la)?\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\s+(\w+(?:\s+\w+)?)',
                        # "dónde está la zona depósito 3"
                        r'd(ó|o)nde\s+(?:est(a|á)|queda|se\s+encuentra|se\s+ubica)\s+(?:el|la)?\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                        # "ubicación de depósito 3"
                        r'ubicaci(o|ó)n\s+(?:del|de\s+la|de)\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                        # "dirección de depósito 3"
                        r'direcci(o|ó)n\s+(?:del|de\s+la|de)\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                    ]
                    
                    for patron in patrones_extraccion:
                        match = re.search(patron, mensaje_lower, re.IGNORECASE)
                        if match:
                            grupos = match.groups()
                            if grupos:
                                nombre_extraido = grupos[-1].strip()
                                nombre_extraido = re.sub(r'[?.,!;:]+$', '', nombre_extraido).strip()
                                if nombre_extraido:
                                    break
                    
                    # Si no se extrajo con patrones, intentar limpiar el texto
                    if not nombre_extraido:
                        texto_limpio = mensaje_lower
                        palabras_limpiar = ['donde', 'esta', 'está', 'queda', 'se encuentra', 'se ubica', 
                                           'ubicacion', 'ubicación', 'direccion', 'dirección', 'domicilio',
                                           'cual', 'cuál', 'es', 'la', 'el', 'del', 'de la', 'de', 'zona']
                        for palabra in palabras_limpiar:
                            texto_limpio = texto_limpio.replace(palabra, ' ')
                        nombre_extraido = ' '.join(texto_limpio.split()).strip()
                        nombre_extraido = re.sub(r'[?.,!;:]+$', '', nombre_extraido).strip()
                    
                    if nombre_extraido:
                        zona_encontrada = ejecutor._buscar_zona_por_nombre(nombre_extraido, usuario)
                        if zona_encontrada:
                            print(f"📍 [VERIFICACIÓN PREVIA] Detectada palabra 'zona' y encontrada zona '{zona_encontrada[0].nombre}' - cambiando a UBICACION_ZONA")
                            tipo_consulta = 'UBICACION_ZONA'
                            variables['zona'] = nombre_extraido
                            variables.pop('movil', None)  # Remover móvil si estaba
                            # Buscar vector de UBICACION_ZONA
                            for vector_db in vectores:
                                if vector_db.tipo_consulta == 'UBICACION_ZONA' and vector_db.activo:
                                    vector_usado = vector_db
                                    break
            
            # Para LLEGADA, NO extraer móvil del texto (evitar confundir con direcciones)
            # SOLO usar el que viene del vector o el contexto
            if tipo_consulta != 'LLEGADA' and tipo_consulta != 'UBICACION_ZONA':
                # Intentar extraer móvil del texto actual (siempre) para permitir reemplazar contexto
                movil_actual = (variables.get('movil') or '').strip()
                palabras_comunes = {'donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con'}

                import unicodedata

                # Normalizar texto (quitar acentos) y convertir a minúsculas para procesamiento
                texto_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', mensaje)
                    if unicodedata.category(c) != 'Mn'
                ).lower()
                
                # Convertir números escritos en letras a dígitos ANTES de extraer móvil
                numeros_texto = {
                    'cero': '0', 'uno': '1', 'una': '1', 'dos': '2', 'tres': '3',
                    'cuatro': '4', 'cinco': '5', 'seis': '6', 'siete': '7',
                    'ocho': '8', 'nueve': '9', 'diez': '10', 'once': '11',
                    'doce': '12', 'trece': '13', 'catorce': '14', 'quince': '15',
                    'dieciseis': '16', 'dieciséis': '16', 'diecisiete': '17',
                    'dieciocho': '18', 'diecinueve': '19', 'veinte': '20'
                }
                
                pattern_numeros = r'\b(' + '|'.join(sorted(numeros_texto.keys(), key=len, reverse=True)) + r')\b'
                
                def reemplazo_numero(match):
                    palabra = match.group(0)
                    return numeros_texto.get(palabra, palabra)
                
                texto_normalizado = re.sub(pattern_numeros, reemplazo_numero, texto_normalizado)
                print(f"🔢 Texto después de convertir números: '{texto_normalizado}'")

                movil_extraido = None
                # Primero intentar patentes tipo "AA285TA", "JGI640" (letras-números-letras)
                patron_patente_letras_num_letras = r'\b([a-z]{2,3})\s*(\d{2,4})\s*([a-z]{1,3})\b'
                match = re.search(patron_patente_letras_num_letras, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_extraido = (match.group(1) + match.group(2) + match.group(3)).upper()
                    print(f"✅ Móvil extraído del texto (patente letras-num-letras): '{movil_extraido}'")
                else:
                    # Intentar patentes tipo "ASN773", "OVV799" (letras-números)
                    patron_patente = r'\b([a-z]{2,4})\s*(\d{2,4})\b'
                    match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                    if match:
                        movil_extraido = (match.group(1) + match.group(2)).upper()
                        print(f"✅ Móvil extraído del texto (patente): '{movil_extraido}'")
                    else:
                        # Buscar nombres tipo "camion3", "camion 3", "auto2", etc.
                        # Patrón más flexible que busca palabras seguidas de números
                        patron_nombre = r'\b(camion|auto|vehiculo|movil|unidad|truck|carro|moto)\s*(\d+)\b'
                        match = re.search(patron_nombre, texto_normalizado, re.IGNORECASE)
                        if match:
                            # Normalizar: siempre usar la primera palabra del match (camion/auto/etc) + número
                            prefijo = match.group(1).lower()
                            numero = match.group(2)
                            # Normalizar prefijos comunes
                            if prefijo in ['camion', 'truck']:
                                prefijo = 'CAMION'
                            elif prefijo == 'movil' or prefijo == 'móvil':
                                prefijo = 'MOVIL'  # "movil" debe normalizarse a "MOVIL", no a "AUTO"
                            elif prefijo in ['auto', 'vehiculo', 'carro', 'unidad']:
                                prefijo = 'AUTO'
                            elif prefijo == 'moto':
                                prefijo = 'MOTO'
                            movil_extraido = f"{prefijo}{numero}"
                            print(f"✅ Móvil extraído del texto (nombre normalizado): '{movil_extraido}'")
                        else:
                            # Patrón genérico como fallback (palabra + número)
                            patron_generico = r'\b([a-z]{3,})\s*(\d+)\b'
                            match = re.search(patron_generico, texto_normalizado, re.IGNORECASE)
                            if match:
                                movil_extraido = (match.group(1) + match.group(2)).upper()
                                print(f"⚠️ Móvil extraído del texto (genérico): '{movil_extraido}'")
                            else:
                                print(f"⚠️ No se pudo extraer móvil del texto normalizado: '{texto_normalizado}'")

                if movil_extraido:
                    if not movil_actual or movil_actual.upper() != movil_extraido:
                        variables['movil'] = movil_extraido
                        movil_actual = movil_extraido
            
            # Para TODOS los tipos (incluyendo LLEGADA): si no hay móvil, usar contexto
            # Obtener valor actual de móvil (puede haber sido extraído arriba)
            movil_actual = (variables.get('movil') or '').strip()
            palabras_comunes = {'donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con'}
            
            # SOLO SI NO SE ENCONTRÓ MÓVIL EN EL TEXTO ACTUAL: usar contexto
            if not movil_actual or movil_actual.lower() in palabras_comunes:
                # Usar el contexto mejorado si está disponible
                if contexto.get('ultimo_movil'):
                    print(f"Usando contexto: último móvil consultado fue '{contexto['ultimo_movil']}'")
                    variables['movil'] = contexto['ultimo_movil']
                    variables['movil_referencia'] = contexto['ultimo_movil']
                    variables['_usando_contexto'] = True
                else:
                    # Fallback a la función anterior
                    ultimo_movil = _obtener_ultimo_movil_contexto(usuario)
                    if ultimo_movil:
                        print(f"Usando contexto (fallback): último móvil consultado fue '{ultimo_movil}'")
                        variables['movil'] = ultimo_movil
                        variables['movil_referencia'] = ultimo_movil
                        variables['_usando_contexto'] = True
                    else:
                        print("No se encontró móvil en texto actual ni en contexto")
                        variables.pop('movil', None)
                        variables.pop('movil_referencia', None)
            else:
                print(f"Usando móvil extraído del texto actual: '{movil_actual}' (sin contexto)")
            
            print(f"Intentando guardar conversación con vector_usado: {vector_usado}")
            
            # Pasar usuario a variables para búsqueda de zonas (solo ID, no el objeto completo)
            if usuario:
                variables['_usuario'] = usuario  # Se usa para búsqueda de zonas, pero se removerá antes de guardar
            
            # PRIORIDAD FINAL: Si es POSICION y no se encontró móvil, o si hay palabra "zona" en el texto,
            # verificar si es una consulta de ubicación de zona
            if tipo_consulta == 'POSICION' and not variables.get('movil'):
                # Verificar si hay palabra "zona" en el texto o patrones de ubicación
                tiene_palabra_zona = re.search(r'\b(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\b', mensaje_lower, re.IGNORECASE)
                tiene_patron_ubicacion = any(re.search(patron, mensaje_lower, re.IGNORECASE) for patron in [
                    r'd(ó|o)nde\s+(?:est(a|á)|queda|se\s+encuentra|se\s+ubica)',
                    r'ubicaci(o|ó)n\s+(?:del|de\s+la|de)',
                    r'direcci(o|ó)n\s+(?:del|de\s+la|de)',
                    r'domicilio\s+(?:del|de\s+la|de)',
                    r'cu(a|á)l\s+es\s+(?:la\s+)?(?:ubicaci(o|ó)n|direcci(o|ó)n|domicilio)',
                ])
                
                if tiene_palabra_zona or tiene_patron_ubicacion:
                    # Intentar extraer nombre y buscar como zona
                    nombre_extraido = None
                    
                    # Si hay palabra "zona", extraer lo que viene después
                    if tiene_palabra_zona:
                        patrones_extraccion = [
                            r'(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\s+(\w+(?:\s+\w+)?)',
                            r'd(ó|o)nde\s+(?:est(a|á)|queda|se\s+encuentra|se\s+ubica)\s+(?:el|la)?\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                            r'ubicaci(o|ó)n\s+(?:del|de\s+la|de)\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                            r'direcci(o|ó)n\s+(?:del|de\s+la|de)\s*(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)?\s*(.+)',
                        ]
                        
                        for patron in patrones_extraccion:
                            match = re.search(patron, mensaje_lower, re.IGNORECASE)
                            if match:
                                grupos = match.groups()
                                if grupos:
                                    nombre_extraido = grupos[-1].strip()
                                    nombre_extraido = re.sub(r'[?.,!;:]+$', '', nombre_extraido).strip()
                                    if nombre_extraido:
                                        break
                    
                    # Si no se extrajo con patrones, intentar limpiar el texto
                    if not nombre_extraido and tiene_patron_ubicacion:
                        texto_limpio = mensaje_lower
                        palabras_limpiar = ['donde', 'esta', 'está', 'queda', 'se encuentra', 'se ubica', 
                                           'ubicacion', 'ubicación', 'direccion', 'dirección', 'domicilio',
                                           'cual', 'cuál', 'es', 'la', 'el', 'del', 'de la', 'de', 'zona']
                        for palabra in palabras_limpiar:
                            texto_limpio = texto_limpio.replace(palabra, ' ')
                        nombre_extraido = ' '.join(texto_limpio.split()).strip()
                        nombre_extraido = re.sub(r'[?.,!;:]+$', '', nombre_extraido).strip()
                    
                    # Si tenemos un nombre, buscar como zona
                    if nombre_extraido:
                        zona_encontrada = ejecutor._buscar_zona_por_nombre(nombre_extraido, usuario)
                        if zona_encontrada:
                            print(f"📍 [PRIORIDAD FINAL] POSICION sin móvil pero encontrada zona '{zona_encontrada[0].nombre}' - cambiando a UBICACION_ZONA")
                            tipo_consulta = 'UBICACION_ZONA'
                            variables['zona'] = nombre_extraido
                            variables.pop('movil', None)  # Remover móvil si estaba
                            # Buscar vector de UBICACION_ZONA
                            for vector_db in vectores:
                                if vector_db.tipo_consulta == 'UBICACION_ZONA' and vector_db.activo:
                                    vector_usado = vector_db
                                    break
            
            # VERIFICACIÓN FINAL: Si es POSICION y hay un móvil, verificar que exista
            # Si no existe, intentar buscar como zona antes de ejecutar la acción
            if tipo_consulta == 'POSICION' and variables.get('movil'):
                movil_nombre = (variables.get('movil') or '').strip()
                if movil_nombre:
                    # Verificar si el móvil existe en la base de datos (usando los mismos campos que acciones.py)
                    movil_existe = Movil.objects.filter(
                        Q(patente__icontains=movil_nombre) |
                        Q(alias__icontains=movil_nombre) |
                        Q(codigo__icontains=movil_nombre)
                    ).exists()
                    
                    if not movil_existe:
                        print(f"⚠️ [VERIFICACIÓN FINAL] Móvil '{movil_nombre}' no existe en BD, verificando si es zona...")
                        # Intentar buscar como zona
                        zona_encontrada = ejecutor._buscar_zona_por_nombre(movil_nombre, usuario)
                        if zona_encontrada:
                            print(f"📍 [VERIFICACIÓN FINAL] '{movil_nombre}' es una zona, cambiando a UBICACION_ZONA")
                            tipo_consulta = 'UBICACION_ZONA'
                            variables['zona'] = movil_nombre
                            variables.pop('movil', None)
                            # Buscar vector de UBICACION_ZONA
                            for vector_db in vectores:
                                if vector_db.tipo_consulta == 'UBICACION_ZONA' and vector_db.activo:
                                    vector_usado = vector_db
                                    break
            
            # Ejecutar acción
            try:
                respuesta_raw = ejecutor.ejecutar(tipo_consulta, variables)
            except Exception as e:
                print(f"❌ Error ejecutando acción {tipo_consulta}: {e}")
                import traceback
                traceback.print_exc()
                respuesta_raw = {
                    'texto': f"Error al procesar la consulta: {str(e)}",
                    'audio': "Ocurrió un error al procesar tu consulta."
                }
            
            # Manejar respuesta con estructura nueva (texto/audio) o respuesta simple (string)
            if isinstance(respuesta_raw, dict):
                respuesta = respuesta_raw.get('texto', str(respuesta_raw))
                respuesta_audio = respuesta_raw.get('audio', respuesta)
                google_maps_link = respuesta_raw.get('google_maps_link', None)
                whatsapp_data = respuesta_raw.get('whatsapp_data', None)
            else:
                respuesta = respuesta_raw
                respuesta_audio = respuesta
                google_maps_link = None
                whatsapp_data = None
            
            print(f"📝 Respuesta generada: {respuesta[:100]}...")
            
            # Limpiar variables antes de guardar y usar en respuesta (remover objetos no serializables)
            variables_para_guardar = variables.copy()
            # Asegurar que el tipo de consulta se guarde para el contexto
            if tipo_consulta:
                variables_para_guardar['tipo_consulta'] = tipo_consulta
            # Asegurar que el móvil se guarde si existe
            if variables.get('movil'):
                variables_para_guardar['movil'] = variables.get('movil')
            # Remover el objeto User si existe (no es serializable a JSON)
            if '_usuario' in variables_para_guardar:
                # Guardar solo el ID del usuario si existe
                if variables_para_guardar['_usuario']:
                    variables_para_guardar['_usuario_id'] = variables_para_guardar['_usuario'].id
                del variables_para_guardar['_usuario']
            
            # Guardar conversación (si está disponible)
            try:
                # Obtener usuario si está autenticado
                usuario = None
                if hasattr(request, 'user') and request.user.is_authenticated:
                    usuario = request.user
                
                print(f"👤 Usuario: {usuario}")
                print(f"💬 Mensaje: {mensaje}")
                print(f"🤖 Respuesta: {respuesta[:50]}...")
                print(f"📊 Similitud: {similitud}")
                print(f"🔗 Vector usado: {vector_usado}")
                
                conversacion = ConversacionSofia.objects.create(
                    usuario=usuario,
                    mensaje_usuario=mensaje,
                    respuesta_sofia=respuesta,
                    vector_usado=vector_usado,
                    similitud=similitud,
                    datos_consulta=variables_para_guardar
                )
                print(f"✅ Conversación guardada exitosamente: ID {conversacion.id}")
            except Exception as e:
                print(f"No se pudo guardar la conversación: {e}")
                import traceback
                traceback.print_exc()
            
            # Construir respuesta JSON
            duration = time.time() - start_time
            if duration > 1.0:
                print(f"⚠️ Sofia tardó {duration:.2f}s en procesar consulta")
            
            # Construir respuesta JSON
            response_data = {
                'success': True,
                'respuesta': respuesta,
                'respuesta_audio': respuesta_audio,
                'google_maps_link': google_maps_link,
                'tiempo_procesamiento': round(duration, 2),
                'whatsapp_data': whatsapp_data,
                'datos_consulta': variables_para_guardar,  # Usar variables limpias
                'historial_sugerencias': historial_recorridos,
                'usando_contexto': variables.get('_usando_contexto', False)
            }

            # Agregar link de Google Maps si existe (ya está en el dict, pero por si acaso)
            if google_maps_link:
                response_data['google_maps_link'] = google_maps_link
            
            # Agregar datos de WhatsApp si existen (ya está en el dict, pero por si acaso)
            if whatsapp_data:
                response_data['whatsapp_data'] = whatsapp_data
            
            return JsonResponse(response_data)
        else:
            # PRIORIDAD 0: Detectar frases comunes de cortesía/confirmación (solo si no se encontró consulta válida)
            frases_comunes = [
                'ok', 'okay', 'okey', 'okey dokey',
                'gracias', 'muchas gracias', 'muchísimas gracias', 'gracias a vos', 'gracias a ti',
                'de nada', 'no hay de qué', 'por nada', 'a vos', 'a ti',
                'perfecto', 'perfecto gracias', 'perfecto, gracias',
                'genial', 'genial gracias', 'genial, gracias',
                'excelente', 'excelente gracias', 'excelente, gracias',
                'bien', 'muy bien', 'está bien', 'esta bien',
                'entendido', 'entendido gracias', 'entendido, gracias',
                'listo', 'listo gracias', 'listo, gracias',
                'dale', 'dale gracias', 'dale, gracias',
                'bueno', 'bueno gracias', 'bueno, gracias',
                'vale', 'vale gracias', 'vale, gracias',
                'si', 'sí', 'si gracias', 'sí gracias', 'si, gracias', 'sí, gracias',
                'claro', 'claro gracias', 'claro, gracias',
                'por supuesto', 'por supuesto gracias', 'por supuesto, gracias',
                'de acuerdo', 'de acuerdo gracias', 'de acuerdo, gracias',
                'bárbaro', 'barbaro', 'bárbaro gracias', 'barbaro gracias',
                'joya', 'joya gracias', 'joya, gracias',
                'buenísimo', 'buenisimo', 'buenísimo gracias', 'buenisimo gracias',
            ]
            
            # Verificar si es una frase común (solo si no tiene palabras de consulta y es corta)
            es_frase_comun = (any(frase in mensaje_lower for frase in frases_comunes) and 
                             not tiene_palabra_consulta and 
                             len(mensaje_lower.split()) <= 4)
            
            # Responder a frases comunes
            if es_frase_comun:
                import random
                # Respuestas variadas según el tipo de frase
                if any(palabra in mensaje_lower for palabra in ['gracias', 'muchas gracias', 'muchísimas gracias']):
                    respuestas_gracias = [
                        "¡De nada! 😊 ¿Algo más en lo que pueda ayudarte?",
                        "¡Por nada! 👋 Estoy aquí para lo que necesites.",
                        "¡A vos! 😊 Cualquier consulta, no dudes en preguntarme.",
                        "¡De nada! 😊 Fue un placer ayudarte.",
                        "¡No hay de qué! 👋 ¿Necesitas algo más?",
                        "¡Para eso estoy! 😊 ¿En qué más puedo ayudarte?"
                    ]
                    respuesta = random.choice(respuestas_gracias)
                elif any(palabra in mensaje_lower for palabra in ['ok', 'okay', 'okey', 'entendido', 'listo', 'dale', 'claro', 'si', 'sí', 'de acuerdo']):
                    respuestas_confirmacion = [
                        "Perfecto 😊 ¿En qué más puedo ayudarte?",
                        "¡Genial! 👋 ¿Necesitas algo más?",
                        "De acuerdo 😊 ¿Alguna otra consulta?",
                        "¡Listo! 👋 Estoy aquí cuando me necesites.",
                        "Perfecto 😊 ¿Qué más necesitas?",
                        "¡Bien! 👋 ¿Algo más?"
                    ]
                    respuesta = random.choice(respuestas_confirmacion)
                else:
                    respuestas_genericas = [
                        "¡Perfecto! 😊 ¿En qué más puedo ayudarte?",
                        "¡Genial! 👋 ¿Necesitas algo más?",
                        "De acuerdo 😊 ¿Alguna otra consulta?",
                        "¡Bien! 👋 Estoy aquí cuando me necesites.",
                        "Perfecto 😊 ¿Qué más necesitas?"
                    ]
                    respuesta = random.choice(respuestas_genericas)
                
                return JsonResponse({
                    'success': True,
                    'respuesta': respuesta,
                    'respuesta_audio': respuesta,
                    'es_frase_comun': True
                })
            
            # No se encontró coincidencia (consulta no interpretada)
            respuesta = "No entiendo la consulta"
            
            # Guardar conversación sin coincidencia (si está disponible)
            try:
                # Obtener usuario si está autenticado
                usuario = None
                if hasattr(request, 'user') and request.user.is_authenticated:
                    usuario = request.user
                
                print(f"👤 Usuario: {usuario}")
                print(f"💬 Mensaje (sin interpretar): {mensaje}")
                print(f"🤖 Respuesta: {respuesta}")
                print(f"📊 Similitud: 0.0")
                
                conversacion = ConversacionSofia.objects.create(
                    usuario=usuario,
                    mensaje_usuario=mensaje,
                    respuesta_sofia=respuesta,
                    similitud=0.0
                )
                print(f"✅ Conversación guardada exitosamente (sin coincidencia): ID {conversacion.id}")
            except Exception as e:
                print(f"⚠️ No se pudo guardar conversación: {e}")
                import traceback
                traceback.print_exc()
            
            duration = time.time() - start_time
            if duration > 1.0:
                print(f"⚠️ Sofia tardó {duration:.2f}s en procesar consulta")
            
            return JsonResponse({
                'success': True,
                'respuesta': respuesta,
                'similitud': 0.0,
                'tiempo_procesamiento': round(duration, 2)
            })
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Error procesando consulta: {e} (tardó {duration:.2f}s)")
        import traceback
        traceback.print_exc()
        # Devolver respuesta de error más amigable
        return JsonResponse({
            'success': False,
            'respuesta': f"Ocurrió un error al procesar tu consulta: {str(e)}",
            'respuesta_audio': "Ocurrió un error. Por favor intenta nuevamente.",
            'error': str(e),
            'tiempo_procesamiento': round(duration, 2)
        }, status=500)

