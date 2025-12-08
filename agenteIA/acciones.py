"""
Módulo para ejecutar acciones basadas en consultas
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone
from moviles.models import Movil, MovilStatus, MovilGeocode
from zonas.models import Zona
from django.contrib.auth.models import User
import re
import requests
from math import radians, cos, sin, asin, sqrt
import unicodedata


class EjecutorAcciones:
    """
    Ejecuta acciones basadas en el tipo de consulta
    """
    
    def __init__(self):
        pass
    
    def _reemplazar_numeros_texto(self, texto: str) -> str:
        """
        Reemplaza números escritos en palabras por su equivalente numérico.
        Ej: 'camion dos' -> 'camion 2'
        """
        if not texto:
            return texto
        
        numeros_texto = {
            'cero': '0',
            'uno': '1',
            'una': '1',
            'dos': '2',
            'tres': '3',
            'cuatro': '4',
            'cinco': '5',
            'seis': '6',
            'siete': '7',
            'ocho': '8',
            'nueve': '9',
            'diez': '10',
            'once': '11',
            'doce': '12',
            'trece': '13',
            'catorce': '14',
            'quince': '15',
            'dieciseis': '16',
            'dieciséis': '16',
            'diecisiete': '17',
            'dieciocho': '18',
            'diecinueve': '19',
            'veinte': '20'
        }
        
        pattern = r'\b(' + '|'.join(sorted(numeros_texto.keys(), key=len, reverse=True)) + r')\b'
        
        def reemplazo(match):
            palabra = match.group(0)
            return numeros_texto.get(palabra, palabra)
        
        return re.sub(pattern, reemplazo, texto)
    
    def _normalizar_nombre_zona(self, nombre: str) -> str:
        """
        Normaliza un nombre de zona para comparación flexible:
        - Convierte a minúsculas
        - Remueve acentos/tildes
        - Convierte números escritos en letras a dígitos (ej: "tres" -> "3")
        - Normaliza espacios (quita espacios entre letras y números, ej: "DEPOSITO 2" -> "DEPOSITO2")
        - Quita espacios múltiples
        """
        if not nombre:
            return ""
        
        # Convertir a minúsculas
        nombre_lower = nombre.lower().strip()
        
        # Remover acentos/tildes
        nombre_sin_acentos = ''.join(
            c for c in unicodedata.normalize('NFD', nombre_lower)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Convertir números escritos en letras a dígitos
        numeros_en_letras = {
            'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
            'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9',
            'diez': '10', 'once': '11', 'doce': '12', 'trece': '13', 'catorce': '14',
            'quince': '15', 'dieciseis': '16', 'diecisiete': '17', 'dieciocho': '18',
            'diecinueve': '19', 'veinte': '20', 'veintiuno': '21', 'veintidos': '22',
            'veintitres': '23', 'veinticuatro': '24', 'veinticinco': '25',
            'veintiseis': '26', 'veintisiete': '27', 'veintiocho': '28',
            'veintinueve': '29', 'treinta': '30'
        }
        
        # Reemplazar números escritos en letras por dígitos
        # Usar word boundaries para evitar reemplazar partes de palabras
        for palabra, numero in numeros_en_letras.items():
            # Buscar la palabra completa (con límites de palabra)
            patron = r'\b' + re.escape(palabra) + r'\b'
            nombre_sin_acentos = re.sub(patron, numero, nombre_sin_acentos, flags=re.IGNORECASE)
        
        # Normalizar espacios: quitar espacios entre letras y números
        # Ej: "DEPOSITO 2" -> "DEPOSITO2", "ZONA 5" -> "ZONA5", "deposito 3" -> "deposito3"
        nombre_normalizado = re.sub(r'([a-z])\s+(\d)', r'\1\2', nombre_sin_acentos)
        nombre_normalizado = re.sub(r'(\d)\s+([a-z])', r'\1\2', nombre_normalizado)
        
        # Quitar espacios múltiples y espacios al inicio/final
        nombre_normalizado = re.sub(r'\s+', ' ', nombre_normalizado).strip()
        
        return nombre_normalizado
    
    def _buscar_zona_por_nombre(self, nombre_busqueda: str, usuario: Optional[User] = None) -> Optional[Tuple[Zona, float, float, str]]:
        """
        Busca una zona por nombre con coincidencia flexible.
        Normaliza nombres para que "DEPOSITO2" y "DEPOSITO 2" sean iguales.
        
        Args:
            nombre_busqueda: Nombre o parte del nombre de la zona a buscar
            usuario: Usuario para filtrar zonas (opcional, no se usa actualmente)
            
        Returns:
            Tupla (Zona, latitud, longitud, nombre) si encuentra, None si no
        """
        try:
            if not nombre_busqueda or not nombre_busqueda.strip():
                return None
            
            nombre_busqueda = nombre_busqueda.strip()
            print(f"🔍 Buscando zona: '{nombre_busqueda}'")
            
            # Normalizar nombre de búsqueda
            nombre_busqueda_normalizado = self._normalizar_nombre_zona(nombre_busqueda)
            print(f"🔍 Nombre normalizado: '{nombre_busqueda_normalizado}'")
            
            # Buscar zonas visibles (equivalente a activas)
            # Optimizar consulta de zonas - solo campos necesarios
            zonas_query = Zona.objects.filter(visible=True).only('id', 'nombre', 'centro', 'geom', 'tipo', 'direccion', 'direccion_formateada')
            zonas = list(zonas_query.all())  # Evaluar queryset de una vez
            print(f"🔍 Zonas disponibles: {[z.nombre for z in zonas]}")
            
            mejor_coincidencia = None
            mejor_puntaje = 0
            
            for zona in zonas:
                # Normalizar nombre de la zona
                nombre_zona_normalizado = self._normalizar_nombre_zona(zona.nombre)
                
                # Calcular puntaje de coincidencia
                puntaje = 0
                
                # Coincidencia exacta después de normalización (mayor puntaje)
                if nombre_zona_normalizado == nombre_busqueda_normalizado:
                    puntaje = 100
                    print(f"  ✅ Coincidencia exacta: '{zona.nombre}' (normalizado: '{nombre_zona_normalizado}')")
                # La búsqueda está contenida en el nombre de la zona
                elif nombre_busqueda_normalizado in nombre_zona_normalizado:
                    # Puntaje basado en qué tan cerca del inicio está
                    posicion = nombre_zona_normalizado.find(nombre_busqueda_normalizado)
                    puntaje = 80 - (posicion * 2)  # Más cerca del inicio = mayor puntaje
                    print(f"  📍 Coincidencia parcial: '{zona.nombre}' (normalizado: '{nombre_zona_normalizado}', puntaje: {puntaje})")
                # El nombre de la zona está contenido en la búsqueda
                elif nombre_zona_normalizado in nombre_busqueda_normalizado:
                    puntaje = 70
                    print(f"  📍 Coincidencia inversa: '{zona.nombre}' (normalizado: '{nombre_zona_normalizado}', puntaje: {puntaje})")
                # Coincidencia parcial (palabras) - solo si ambos tienen espacios
                else:
                    # Dividir en palabras (sin espacios, usar caracteres alfanuméricos)
                    palabras_busqueda = set(re.findall(r'[a-z]+|\d+', nombre_busqueda_normalizado))
                    palabras_zona = set(re.findall(r'[a-z]+|\d+', nombre_zona_normalizado))
                    palabras_comunes = palabras_busqueda.intersection(palabras_zona)
                    if palabras_comunes:
                        # Puntaje basado en porcentaje de palabras comunes
                        porcentaje = len(palabras_comunes) / max(len(palabras_busqueda), len(palabras_zona))
                        puntaje = int(porcentaje * 60)
                        if puntaje >= 50:
                            print(f"  📍 Coincidencia por palabras: '{zona.nombre}' (palabras comunes: {palabras_comunes}, puntaje: {puntaje})")
                
                # Actualizar mejor coincidencia
                if puntaje > mejor_puntaje and puntaje >= 50:  # Umbral mínimo de 50
                    mejor_puntaje = puntaje
                    mejor_coincidencia = zona
            
            if mejor_coincidencia:
                print(f"✅ Zona encontrada: '{mejor_coincidencia.nombre}' (puntaje: {mejor_puntaje})")
                # Obtener coordenadas del centro de la zona
                if mejor_coincidencia.centro:
                    latitud = float(mejor_coincidencia.centro.y)
                    longitud = float(mejor_coincidencia.centro.x)
                else:
                    # Si no tiene centro, usar el centroide de la geometría
                    if mejor_coincidencia.geom:
                        try:
                            centroide = mejor_coincidencia.geom.centroid
                            latitud = float(centroide.y)
                            longitud = float(centroide.x)
                        except (OSError, AttributeError) as e:
                            # GDAL no disponible o error al acceder a geom
                            print(f"⚠️ Error al obtener centroide de zona '{mejor_coincidencia.nombre}': {e}")
                            # Intentar usar dirección si está disponible
                            if hasattr(mejor_coincidencia, 'direccion') and mejor_coincidencia.direccion:
                                # Si tiene dirección, devolver None y que el llamador maneje
                                print(f"⚠️ Zona '{mejor_coincidencia.nombre}' no tiene coordenadas válidas")
                                return None
                            else:
                                print(f"⚠️ Zona '{mejor_coincidencia.nombre}' no tiene coordenadas")
                                return None
                    else:
                        print(f"⚠️ Zona '{mejor_coincidencia.nombre}' no tiene coordenadas")
                        return None
                
                return (
                    mejor_coincidencia,
                    latitud,
                    longitud,
                    mejor_coincidencia.nombre
                )
            
            print(f"⚠️ No se encontró zona con nombre similar a '{nombre_busqueda}' (normalizado: '{nombre_busqueda_normalizado}')")
            return None
        except Exception as e:
            print(f"⚠️ Error en _buscar_zona_por_nombre: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def ejecutar(self, tipo_consulta: str, variables: Dict[str, str]) -> str:
        """
        Ejecuta la acción correspondiente al tipo de consulta
        
        Args:
            tipo_consulta: Tipo de consulta (POSICION, RECORRIDO, etc.)
            variables: Variables extraídas de la consulta
            
        Returns:
            Respuesta formateada para el usuario
        """
        try:
            if tipo_consulta == 'POSICION':
                return self._obtener_posicion_actual(variables)
            elif tipo_consulta == 'RECORRIDO':
                return self._obtener_recorrido(variables)
            elif tipo_consulta == 'ESTADO':
                return self._obtener_estado(variables)
            elif tipo_consulta == 'COMANDO_WHATSAPP':
                return self._comando_whatsapp(variables)
            elif tipo_consulta == 'LLEGADA':
                return self._calcular_llegada(variables)
            elif tipo_consulta == 'CERCANIA':
                return self._obtener_cercania(variables)
            elif tipo_consulta == 'UBICACION_ZONA':
                return self._obtener_ubicacion_zona(variables)
            elif tipo_consulta == 'SALUDO':
                return self._responder_saludo()
            elif tipo_consulta == 'LISTADO_ACTIVOS':
                return self._listar_activos(variables)
            elif tipo_consulta == 'SITUACION_FLOTA':
                return self._situacion_flota(variables)
            elif tipo_consulta == 'MOVILES_EN_ZONA':
                return self._moviles_en_zona(variables)
            elif tipo_consulta == 'MOVILES_FUERA_DE_ZONA':
                return self._moviles_fuera_de_zona(variables)
            elif tipo_consulta == 'INGRESO_A_ZONA':
                return self._ingreso_a_zona(variables)
            elif tipo_consulta == 'SALIO_DE_ZONA':
                return self._salio_de_zona(variables)
            elif tipo_consulta == 'PASO_POR_ZONA':
                return self._paso_por_zona(variables)
            elif tipo_consulta == 'AYUDA_GENERAL':
                return self._responder_ayuda(variables)
            elif tipo_consulta == 'VER_MAPA':
                return self._ver_en_mapa(variables)
            else:
                return {
                    'texto': "Lo siento, no entiendo esa consulta.",
                    'audio': "Disculpame, no entendí esa consulta."
                }
        except Exception as e:
            print(f"❌ Error ejecutando acción: {e}")
            return {
                'texto': "Ocurrió un error al procesar tu consulta.",
                'audio': "Hubo un problema. Intentá nuevamente."
            }
    
    def _obtener_posicion_actual(self, variables: Dict[str, str]) -> str:
        """Obtiene la posición actual de un móvil"""
        # Extraer del dict o intentar buscar en el texto completo si variables no funcionó
        movil_nombre = variables.get('movil', '').upper()
        
        # Si movil_nombre es una palabra muy común como "donde", "que", "el", usar fallback
        palabras_comunes = {'donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con'}
        
        if not movil_nombre or movil_nombre.lower() in palabras_comunes:
            # Buscar patentes tipo OVV799, ASN773, etc, o nombres como camion2
            texto_completo = variables.get('_texto_completo', '')
            print(f"🔍 Extrayendo móvil del texto: '{texto_completo}'")
            
            # Normalizar texto (quitar tildes) para mejor matching
            texto_normalizado = ''.join(
                c for c in unicodedata.normalize('NFD', str(texto_completo))
                if unicodedata.category(c) != 'Mn'
            ).lower()
            texto_normalizado = self._reemplazar_numeros_texto(texto_normalizado)
            
            # Primero intentar patente tipo "ASN 773" o "ASN773"
            patron_patente = r'\b([a-z]{2,4})\s*(\d{2,4})\b'
            match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
            if match:
                # Concatenar letras y números
                movil_nombre = (match.group(1) + match.group(2)).upper()
                print(f"✅ Móvil extraído (patente): '{movil_nombre}'")
            else:
                # Si no es patente, buscar nombres alfanuméricos como "camion2", "auto1", etc.
                patron_nombre = r'\b([a-zA-Z]+)\s*(\d+)\b'
                matches = list(re.finditer(patron_nombre, texto_normalizado, re.IGNORECASE))
                if matches:
                    def _puntaje_match(m):
                        palabra = m.group(1).lower()
                        score = 0
                        keywords = ['camion', 'camioneta', 'camioncito', 'camione', 'movil', 'vehiculo', 'auto', 'camioneta', 'camionc']
                        if any(keyword in palabra for keyword in keywords):
                            score += 100
                        elif len(palabra) >= 3:
                            score += 10
                        # prefer coincidencias más cercanas al final del texto
                        score += m.start() / 1000.0
                        return score
                    
                    best_match = None
                    best_score = float('-inf')
                    for m in matches:
                        score = _puntaje_match(m)
                        if score > best_score:
                            best_score = score
                            best_match = m
                    if best_match:
                        movil_nombre = (best_match.group(1) + best_match.group(2)).lower()
                        print(f"✅ Móvil extraído (nombre): '{movil_nombre}' (puntaje {best_score})")
        
        if not movil_nombre or len(movil_nombre) < 3:
            variables.pop('movil', None)
            return {
                'texto': "No especificaste un móvil. Por ejemplo: 'OVV799' o 'donde está el ASN773'",
                'audio': "No especifiqué un móvil. Decime el nombre del vehículo, por ejemplo OVV799."
            }
        
        # Buscar móvil por patente, alias o código
        try:
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).only('id', 'patente', 'alias', 'codigo', 'gps_id', 'activo').first()
            
            if not movil:
                # Debug: mostrar todos los móviles disponibles para diagnóstico
                todos_moviles = Movil.objects.filter(activo=True).only('patente', 'alias', 'codigo')[:10]
                print(f"⚠️ No se encontró móvil '{movil_nombre}'")
                print(f"📋 Móviles disponibles: {[(m.patente, m.alias, m.codigo) for m in todos_moviles]}")
                
                variables.pop('movil', None)

                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'. ¿Está escrito correctamente?",
                    'audio': f"No encontré el móvil {movil_nombre}. ¿Está escrito correctamente?"
                }
            
            # Guardar el móvil encontrado en variables para contexto
            # Usar el nombre normalizado que se usó para buscar
            if 'movil' not in variables or not variables.get('movil') or variables.get('movil').lower() in ['donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con']:
                variables['movil'] = movil_nombre
            
            # Obtener status y geocodificación con select_related optimizado
            # Obtener status y geocodificación - optimizado con only
            status = MovilStatus.objects.filter(movil=movil).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh', 'fecha_gps', 'ignicion', 'bateria_pct', 'calidad_senal', 'satelites').first()
            geocode = MovilGeocode.objects.filter(movil=movil).only('direccion_formateada', 'localidad', 'provincia').first()
            
            if not status or not status.ultimo_lat:
                movil_nombre = movil.alias or movil.patente
                return {
                    'texto': f"El móvil '{movil_nombre}' no tiene posición actual registrada.",
                    'audio': f"No puedo indicarte la posición de {movil_nombre} ahora. No hay datos recientes."
                }
            
            # Formatear respuesta para texto
            respuesta_texto = f"*{movil.alias or movil.patente}*\n\n"
            
            # Dirección (limpiar para texto y audio)
            if geocode and geocode.direccion_formateada:
                # Limpiar dirección removiendo código postal, "Partido de", "Argentina"
                direccion_limpia = geocode.direccion_formateada
                # Remover código postal (cualquier secuencia de 4-5 dígitos)
                direccion_limpia = re.sub(r'\b\d{4,5}\b', '', direccion_limpia)
                direccion_limpia = direccion_limpia.replace('Partido de La Matanza,', '')
                direccion_limpia = direccion_limpia.replace('Argentina', '')
                direccion_limpia = direccion_limpia.replace(',,', ',')
                direccion_limpia = direccion_limpia.strip().rstrip(',')
                
                respuesta_texto += f"Dirección: {direccion_limpia}\n"
            else:
                direccion_limpia = "ubicación desconocida"
            
            # Última actualización
            if status.fecha_gps:
                respuesta_texto += f"Actualización: {status.fecha_gps.strftime('%d/%m/%Y %H:%M')}"
            
            # Formatear respuesta para audio (más natural y simple)
            movil_nombre = movil.alias or movil.patente
            
            from datetime import date
            
            if status.fecha_gps:
                hora = status.fecha_gps.strftime('%H:%M')
                # Verificar si la actualización es de hoy
                if status.fecha_gps.date() == date.today():
                    fecha_hora = f"a las {hora} de hoy"
                else:
                    fecha = status.fecha_gps.strftime('%d de %B de %Y')
                    fecha_hora = f"el {fecha} a las {hora}"
            else:
                fecha_hora = "fecha desconocida"
            
            respuesta_audio = f"{movil_nombre} está en {direccion_limpia}, {fecha_hora}."
            
            # NO incluir google_maps_link aquí - solo se incluye en VER_MAPA
            # Si el usuario quiere ver en mapa, debe usar el comando explícito "ver en mapa" o "mostrar en mapa"
            
            # Guardar datos adicionales para WhatsApp
            whatsapp_data = {
                'patente': movil.patente,
                'alias': movil.alias,
                'direccion': geocode.direccion_formateada if geocode else 'Sin geocodificación',
                'fecha_actualizacion': status.fecha_gps.strftime('%d/%m/%Y %H:%M') if status.fecha_gps else 'Sin datos',
                'lat': status.ultimo_lat,
                'lon': status.ultimo_lon
            }
            
            # Devolver ambas versiones + datos WhatsApp (sin google_maps_link)
            return {
                'texto': respuesta_texto,
                'audio': respuesta_audio,
                'lat': status.ultimo_lat,
                'lon': status.ultimo_lon,
                'whatsapp_data': whatsapp_data
            }
            
        except Exception as e:
            print(f"Error obteniendo posición: {e}")
            return {
                'texto': "Ocurrió un error al consultar la posición.",
                'audio': "No pude consultar la posición. Intentá nuevamente."
            }
    
    def _parsear_tiempo_relativo(self, texto: str) -> int:
        """
        Parsea expresiones de tiempo relativas como 'hace 10 dias', 'hace 2 semanas', etc.
        Retorna el número de minutos hacia atrás (para mayor precisión)
        """
        import re
        
        texto_lower = texto.lower()
        
        # Limpiar caracteres especiales y normalizar
        texto_clean = re.sub(r'[^\w\s]', ' ', texto_lower)
        
        # Patrones para detectar tiempo relativo
        # "hace X meses/mes"
        match = re.search(r'hace\s+(\d+)\s+(meses|mes)', texto_clean)
        if match:
            meses = int(match.group(1))
            return meses * 30 * 24 * 60  # Convertir meses a minutos (1 mes = 30 días)
        
        # "hace X semanas/semana"
        match = re.search(r'hace\s+(\d+)\s+(semanas|semana)', texto_clean)
        if match:
            return int(match.group(1)) * 7 * 24 * 60  # Convertir semanas a minutos
        
        # "hace X dias/día"
        match = re.search(r'hace\s+(\d+)\s+(dias|día)', texto_clean)
        if match:
            return int(match.group(1)) * 24 * 60  # Convertir días a minutos
        
        # "hace X horas" -> convertir a minutos
        match = re.search(r'hace\s+(\d+)\s+horas?', texto_clean)
        if match:
            horas = int(match.group(1))
            return horas * 60  # Convertir horas a minutos
        
        # "hace X minutos/minuto" -> minutos directamente
        match = re.search(r'hace\s+(\d+)\s+(minutos|minuto)', texto_clean)
        if match:
            return int(match.group(1))  # Ya son minutos
        
        # "ayer" o "hace 1 dia"
        if 'ayer' in texto_lower or texto_clean.replace(' ', '') == 'hace1dia':
            return 1 * 24 * 60  # 1 día en minutos
        
        # "hoy" -> 0 minutos
        if 'hoy' in texto_lower and 'hace' not in texto_lower:
            return 0
        
        # "la semana pasada", "semana pasada"
        if 'semana pasada' in texto_lower:
            return 7 * 24 * 60  # 1 semana en minutos
        
        # "el mes pasado", "mes pasado"
        if 'mes pasado' in texto_lower:
            return 30 * 24 * 60  # 1 mes en minutos (aproximado)
        
        # "hace una semana"
        if 'hace una semana' in texto_lower or 'hace 1 semana' in texto_clean:
            return 7 * 24 * 60
        
        # "hace un mes"
        if 'hace un mes' in texto_lower or 'hace 1 mes' in texto_clean:
            return 30 * 24 * 60
        
        # Si no se detecta nada, asumir "ayer" (comportamiento por defecto)
        return 1 * 24 * 60
    
    def _formatear_periodo(self, minutos_atras: int) -> tuple:
        """
        Convierte un número de minutos hacia atrás en un texto legible (ej: "hace 2 semanas")
        Retorna tupla (texto, audio)
        """
        if minutos_atras == 0:
            return ('hoy', 'hoy')
        elif minutos_atras == 1 * 24 * 60:
            return ('ayer', 'ayer')
        
        # Convertir minutos a unidades más grandes
        dias = minutos_atras // (24 * 60)
        horas = minutos_atras // 60
        minutos = minutos_atras
        
        # Verificar si es un número exacto de meses (aproximado: 30 días)
        if dias % 30 == 0 and dias >= 30:
            meses = dias // 30
            if meses == 1:
                return ('hace 1 mes', 'hace 1 mes')
            else:
                return (f'hace {meses} meses', f'hace {meses} meses')
        
        # Verificar si es un número exacto de semanas (7 días)
        if dias % 7 == 0 and dias >= 7:
            semanas = dias // 7
            if semanas == 1:
                return ('hace 1 semana', 'hace 1 semana')
            else:
                return (f'hace {semanas} semanas', f'hace {semanas} semanas')
        
        # Verificar si es un número exacto de días
        if minutos_atras % (24 * 60) == 0 and dias >= 1:
            if dias == 1:
                return ('hace 1 día', 'hace 1 día')
            else:
                return (f'hace {dias} días', f'hace {dias} días')
        
        # Verificar si es un número exacto de horas
        if minutos_atras % 60 == 0 and horas >= 1:
            if horas == 1:
                return ('hace 1 hora', 'hace 1 hora')
            else:
                return (f'hace {horas} horas', f'hace {horas} horas')
        
        # Días aproximados (para el cálculo de búsqueda)
        if dias >= 1:
            if dias == 1:
                return ('hace 1 día', 'hace 1 día')
            else:
                return (f'hace {dias} días', f'hace {dias} días')
        
        # Horas aproximadas
        if horas >= 1:
            if horas == 1:
                return ('hace 1 hora', 'hace 1 hora')
            else:
                return (f'hace {horas} horas', f'hace {horas} horas')
        
        # Minutos
        if minutos == 1:
            return ('hace 1 minuto', 'hace 1 minuto')
        else:
            return (f'hace {minutos} minutos', f'hace {minutos} minutos')
    
    def _obtener_recorrido(self, variables: Dict[str, str]) -> str:
        """Obtiene el recorrido histórico de un móvil"""
        # Si el texto contiene "donde ESTA" (presente) SIN expresiones de tiempo pasadas, redirigir a posición actual
        texto = variables.get('_texto_completo', '').lower()
        
        # Detectar si hay expresiones de tiempo pasado
        expresiones_pasado = ['hace', 'ayer', 'semana pasada', 'mes pasado', 'estaba', 'estuvo']
        tiene_tiempo_pasado = any(exp in texto for exp in expresiones_pasado)
        
        # Solo redirigir a posición actual si pregunta "donde está" en PRESENTE
        if ('donde esta' in texto or 'donde está' in texto) and not tiene_tiempo_pasado:
            print("🔄 Redirigiendo a posición actual porque pregunta es en presente")
            return self._obtener_posicion_actual(variables)
        
        # Si pregunta "donde estaba/estuvo", es histórica (no redirigir)
        if 'donde estaba' in texto or 'donde estuvo' in texto:
            print("📅 Detectada pregunta histórica con 'donde estaba/estuvo'")
        
        movil_nombre = variables.get('movil', '').upper()
        
        # Si movil_nombre es una palabra muy común como "donde", "que", "el", usar fallback
        palabras_comunes = {'donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con'}
        
        if not movil_nombre or movil_nombre.lower() in palabras_comunes:
            texto_completo = variables.get('_texto_completo', '')
            print(f"🔍 Extrayendo móvil del texto: '{texto_completo}'")
            
            # Normalizar texto (quitar tildes) para mejor matching
            texto_normalizado = ''.join(
                c for c in unicodedata.normalize('NFD', str(texto_completo))
                if unicodedata.category(c) != 'Mn'
            )
            
            # Primero intentar patente tipo "AA285TA", "JGI640" (letras-números-letras)
            patron_patente_letras_num_letras = r'\b([A-Z]{2,3})\s*(\d{2,4})\s*([A-Z]{1,3})\b'
            match = re.search(patron_patente_letras_num_letras, texto_normalizado, re.IGNORECASE)
            if match:
                movil_nombre = (match.group(1) + match.group(2) + match.group(3)).upper()
                print(f"✅ Móvil extraído (patente letras-num-letras): '{movil_nombre}'")
            else:
                # Intentar patente tipo "ASN 773" o "ASN773" (letras-números)
                patron_patente = r'\b([A-Z]{2,4})\s*(\d{2,4})\b'
                match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_nombre = (match.group(1) + match.group(2)).upper()
                    print(f"✅ Móvil extraído (patente): '{movil_nombre}'")
                else:
                    # Si no es patente, buscar nombres alfanuméricos como "camion2", "auto1", etc.
                    patron_nombre = r'\b([a-zA-Z]+)\s*(\d+)\b'
                    match = re.search(patron_nombre, texto_normalizado, re.IGNORECASE)
                    if match:
                        movil_nombre = (match.group(1) + match.group(2)).lower()
                        print(f"✅ Móvil extraído (nombre): '{movil_nombre}'")
        
        if not movil_nombre or len(movil_nombre) < 3:
            return {
                'texto': "No especificaste un móvil.",
                'audio': "Decime qué móvil necesitas consultar."
            }
        
        # Buscar móvil
        try:
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).first()
            
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'.",
                    'audio': f"No encontré el móvil {movil_nombre}. ¿Podrías verificar el nombre?"
                }
            
            # Guardar el móvil encontrado en variables para contexto
            if 'movil' not in variables or not variables.get('movil') or variables.get('movil').lower() in ['donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con']:
                variables['movil'] = movil_nombre
            
            # Obtener posiciones del período especificado
            texto_completo = variables.get('_texto_completo', '')
            minutos_atras = self._parsear_tiempo_relativo(texto_completo)
            print(f"📅 Consultando registros de hace {minutos_atras} minutos")
            
            # Calcular el rango de búsqueda (±10% del tiempo)
            margen = max(minutos_atras // 10, 60)  # Mínimo 60 minutos de margen
            desde = datetime.now() - timedelta(minutes=minutos_atras + margen)
            hasta = datetime.now() - timedelta(minutes=minutos_atras - margen)
            
            from gps.models import Posicion
            # Optimizar consulta de posiciones - solo campos necesarios
            posiciones = Posicion.objects.filter(
                movil=movil,
                fec_gps__gte=desde,
                fec_gps__lte=hasta
            ).only('id', 'fec_gps', 'lat', 'lon', 'velocidad', 'rumbo', 'sats', 'hdop', 'ign_on').order_by('fec_gps')[:500]  # LIMIT 500 para evitar bloquearse
            
            posiciones_list = list(posiciones)  # Convertir QuerySet a lista para poder iterar
            
            if not posiciones_list:
                movil_nombre = movil.alias or movil.patente
                # Crear mensaje descriptivo según el tiempo
                periodo_texto, periodo_audio = self._formatear_periodo(minutos_atras)
                
                return {
                    'texto': f"El móvil '{movil_nombre}' no tiene registros de {periodo_texto}.",
                    'audio': f"No encontré registros de {periodo_audio} para {movil_nombre}."
                }
            
            # Calcular estadísticas
            total_posiciones = len(posiciones_list)
            
            # Calcular distancia aproximada
            distancia_total = 0
            velocidades = []
            
            for i in range(len(posiciones_list) - 1):
                p1 = posiciones_list[i]
                p2 = posiciones_list[i + 1]
                
                # Fórmula de Haversine
                from math import radians, cos, sin, asin, sqrt
                
                def haversine(lon1, lat1, lon2, lat2):
                    R = 6371  # Radio de la Tierra en km
                    dLat = radians(lat2 - lat1)
                    dLon = radians(lon2 - lon1)
                    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                
                distancia_total += haversine(
                    float(p1.lon or 0),
                    float(p1.lat or 0),
                    float(p2.lon or 0),
                    float(p2.lat or 0)
                )
                
                if p1.velocidad:
                    velocidades.append(float(p1.velocidad))
            
            vel_max = max(velocidades) if velocidades else 0
            vel_prom = sum(velocidades) / len(velocidades) if velocidades else 0
            
            # Formatear respuesta con el período apropiado
            movil_nombre = movil.alias or movil.patente
            periodo_texto, periodo_audio = self._formatear_periodo(minutos_atras)
            
            texto = f"📊 *Recorrido de {movil_nombre} ({periodo_texto})*\n\n"
            texto += f"📍 Posiciones: {total_posiciones}\n"
            texto += f"🚗 Distancia: {distancia_total:.2f} km\n"
            texto += f"⚡ Velocidad máx: {vel_max:.0f} km/h\n"
            texto += f"📈 Velocidad promedio: {vel_prom:.0f} km/h"
            
            audio = f"{movil_nombre} {periodo_audio} recorrió {distancia_total:.1f} kilómetros. "
            audio += f"Velocidad máxima {vel_max:.0f} kilómetros por hora y promedio {vel_prom:.0f} kilómetros por hora."
            
            return {"texto": texto, "audio": audio}
            
        except Exception as e:
            print(f"Error obteniendo recorrido: {e}")
            return {
                'texto': "Ocurrió un error al consultar el recorrido.",
                'audio': "No pude consultar el recorrido. Intentá nuevamente."
            }
    
    def _obtener_estado(self, variables: Dict[str, str]) -> str:
        """Obtiene el estado general de un móvil"""
        return self._obtener_posicion_actual(variables)
    
    def _comando_whatsapp(self, variables: Dict[str, str]) -> str:
        """Comando para enviar por WhatsApp - Obtiene posición y prepara para compartir"""
        # Reutilizar la lógica de _obtener_posicion_actual para obtener los datos
        resultado_posicion = self._obtener_posicion_actual(variables)
        
        # Si es un dict (caso normal), agregar mensaje de WhatsApp
        if isinstance(resultado_posicion, dict):
            whatsapp_data = resultado_posicion.get('whatsapp_data', {})
            if whatsapp_data:
                # Agregar mensaje de confirmación
                resultado_posicion['texto'] = "📱 Preparando envío por WhatsApp..."
                resultado_posicion['audio'] = "Preparando el envío de ubicación por WhatsApp."
                # whatsapp_data ya está incluido, el frontend lo manejará
            else:
                # Si no hay datos, usar mensaje de desarrollo
                resultado_posicion = {
                    'texto': "📱 Preparando envío por WhatsApp... (Funcionalidad en desarrollo)",
                    'audio': "La función de compartir por WhatsApp está en desarrollo."
                }
            return resultado_posicion
        else:
            # Si es string (error), mantener el formato
            return {
                'texto': "📱 No pude obtener la ubicación para compartir por WhatsApp.",
                'audio': "No puedo compartir la ubicación ahora."
            }
    
    def _calcular_llegada(self, variables: Dict[str, str]) -> str:
        """Calcula tiempo estimado de llegada usando OSRM + Nominatim (best effort)."""
        try:
            # 1) Identificar móvil
            texto_completo = variables.get('_texto_completo', '')
            movil_nombre = variables.get('movil', '') or ''
            destino_texto = variables.get('destino', '') or ''
            
            # Si hay un destino pero no hay móvil, y el destino parece ser un nombre de zona/móvil,
            # NO intentar extraer el móvil del destino (evitar confundir "deposito2" con un móvil)
            if not movil_nombre and destino_texto:
                # Si el destino parece ser un nombre de zona (no una dirección completa),
                # usar el móvil del contexto si está disponible
                if not any(palabra in destino_texto.lower() for palabra in ['calle', 'avenida', 'av.', 'av ', 'boulevard', 'blv', 'numero', 'nro', ',']):
                    # Parece ser un nombre simple (zona o lugar), no una dirección
                    # Intentar usar el móvil del contexto
                    movil_contexto = variables.get('movil_referencia') or variables.get('_contexto_movil_disponible')
                    if movil_contexto:
                        print(f"📍 Usando móvil del contexto para LLEGADA: '{movil_contexto}'")
                        movil_nombre = movil_contexto
            
            if not movil_nombre:
                # Normalizar texto (quitar tildes) para mejor matching
                texto_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', texto_completo)
                    if unicodedata.category(c) != 'Mn'
                )
                
                # Reusar extractor de patente/alias como en otros métodos
                patron_patente = r"\b([A-Z]{2,4})\s*(\d{2,4})\b"
                match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_nombre = (match.group(1) + match.group(2)).upper()
                else:
                    # Si no es patente, buscar nombres alfanuméricos
                    # PERO: si hay un destino que parece ser un nombre simple, evitar extraerlo como móvil
                    if not destino_texto or any(palabra in destino_texto.lower() for palabra in ['calle', 'avenida', 'av.', 'av ', 'boulevard', 'blv', 'numero', 'nro', ',']):
                        # Solo intentar extraer móvil si no hay destino o el destino parece ser una dirección
                        patron_nombre = r"\b([a-zA-Z]+)\s*(\d+)\b"
                        match = re.search(patron_nombre, texto_normalizado, re.IGNORECASE)
                        if match:
                            candidato_movil = (match.group(1) + match.group(2)).lower()
                            # Verificar que el candidato no sea el mismo que el destino
                            if candidato_movil.upper() != destino_texto.upper():
                                movil_nombre = candidato_movil
            movil_nombre_up = movil_nombre.upper()
            if not movil_nombre_up:
                return {
                    'texto': "No especificaste un móvil.",
                    'audio': "Decime qué móvil necesitas consultar."
                }
            
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre_up) |
                Q(alias__icontains=movil_nombre_up) |
                Q(codigo__icontains=movil_nombre_up)
            ).first()
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre_up}'.", 
                    'audio': f"No encontré el móvil {movil_nombre_up}."
                }
            
            # Guardar el móvil encontrado en variables para contexto
            if 'movil' not in variables or not variables.get('movil') or variables.get('movil').lower() in ['donde', 'que', 'el', 'la', 'los', 'las', 'de', 'del', 'en', 'con']:
                variables['movil'] = movil_nombre_up
            
            status = MovilStatus.objects.filter(movil=movil).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh', 'fecha_gps').first()
            if not status or not status.ultimo_lat or not status.ultimo_lon:
                movil_nombre = movil.alias or movil.patente
                return {
                    'texto': f"El móvil '{movil_nombre}' no tiene posición actual para calcular la llegada.",
                    'audio': f"No puedo calcular la llegada de {movil_nombre}. No hay posición actual."
                }
            
            origen_lat = float(status.ultimo_lat)
            origen_lon = float(status.ultimo_lon)
            
            # 2) Extraer destino
            destino_texto = variables.get('destino')
            if not destino_texto:
                # Normalizar y extraer mejor el destino (ignorar prefijos como "a qué hora podría llegar a ...")
                t = ''.join(c for c in unicodedata.normalize('NFD', texto_completo.lower()) if unicodedata.category(c) != 'Mn')
                t = t.replace(' al ', ' a el ')  # normalizar "al"
                
                # Intentar tomar lo que sigue a la ÚLTIMA ocurrencia de preposición de destino
                destino_texto = None
                for sep in [' a la ', ' a el ', ' a ', ' hasta ', ' hacia ']:
                    if sep in t:
                        destino_texto = t.split(sep)[-1]
                
                if destino_texto:
                    # Limpiar prefijos comunes de pregunta
                    prefijos = [
                        'que hora podria llegar a ', 'a que hora podria llegar a ', 'a que hora llega a ',
                        'cuando llegaria a ', 'cuando llega a ', 'cuando llegaria ', 'cuando llega ',
                        'que hora podria llegar ', 'a que hora podria llegar ',
                        'cuanto tarda en llegar a ', 'cuanto tardaria en llegar a ', 'cuanto tarda en llegar ',
                        'cuanto demora en llegar a ', 'cuanto demoraria en llegar a ', 'cuanto demora en llegar ',
                        'cuanto tardaria hasta ', 'cuanto demoraria hasta ', 'cuanto tarda hasta ', 'cuanto demora hasta ',
                        'en cuanto llegaria ', 'en cuanto llegara ', 'en cuanto llega ',
                    ]
                    for p in prefijos:
                        if destino_texto.startswith(p):
                            destino_texto = destino_texto[len(p):]
                    
                    # Quitar el móvil si quedó al inicio (ej: "asn 773 a rosario")
                    destino_texto = re.sub(r'^([a-z]{2,5}\s*\d{2,5})\s+', '', destino_texto)
                    destino_texto = destino_texto.strip(' ?!.')
                else:
                    destino_texto = ''
            
            # Debug
            print(f"📍 Destino extraído: '{destino_texto}'")
            
            if not destino_texto:
                return {
                    'texto': "No pude identificar el destino. Por ejemplo: 'a Rosario' o 'Av. Corrientes 1234, CABA'.",
                    'audio': "Decime a dónde querés que calcule el arribo."
                }
            
            # 2.5) Buscar primero en zonas de interés antes de geocodificar
            skip_geocode = False
            destino_lat = None
            destino_lon = None
            destino_label = None
            
            if destino_texto and destino_texto.strip():
                try:
                    usuario_consulta = variables.get('_usuario')  # Se puede pasar desde views.py
                    zona_encontrada = self._buscar_zona_por_nombre(destino_texto, usuario_consulta)
                    
                    if zona_encontrada:
                        zona, destino_lat, destino_lon, destino_label = zona_encontrada
                        print(f"📍 Usando zona encontrada: '{zona.nombre}' ({destino_lat}, {destino_lon})")
                        # Si la zona tiene dirección, usarla como label; si no, usar el nombre
                        if zona.direccion_formateada:
                            destino_label = f"{zona.nombre} - {zona.direccion_formateada}"
                        elif zona.direccion:
                            destino_label = f"{zona.nombre} - {zona.direccion}"
                        else:
                            destino_label = zona.nombre
                        # Saltar geocodificación y usar coordenadas de la zona
                        skip_geocode = True
                except Exception as e:
                    print(f"⚠️ Error buscando zona: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continuar con geocodificación normal si falla la búsqueda de zona
                    skip_geocode = False
            
            # 3) Geocodificar destino con Nominatim (solo si no se encontró zona)
            if not skip_geocode:
                # Normalizar dirección para mejorar geocodificación con Nominatim
                def normalizar_direccion(direccion):
                    """
                    Normaliza dirección para mejor matching con Nominatim
                    - Capitaliza palabras importantes
                    - Normaliza abreviaciones
                    - Agrega contexto si falta
                    """
                    # Lista de palabras que NO capitalizar (preposiciones, articulos)
                    no_capitalizar = {'de', 'del', 'y', 'la', 'el', 'las', 'los', 'en', 'por', 'para', 'con', 'sin', 'al', 'a'}
                    
                    # Abreviaciones comunes
                    abreviaciones = {
                        'av': 'Avenida',
                        'av.': 'Avenida',
                        'avda': 'Avenida',
                        'avda.': 'Avenida',
                        'blv': 'Boulevard',
                        'blvr': 'Boulevard',
                        'blvr.': 'Boulevard',
                        'caba': 'Buenos Aires',
                        'bs as': 'Buenos Aires',
                        'cap': 'Buenos Aires',
                        'cap fed': 'Buenos Aires',
                    }
                    
                    # Dividir en palabras
                    palabras = direccion.split()
                    resultado = []
                    
                    for i, palabra in enumerate(palabras):
                        palabra_lower = palabra.lower().rstrip(',').rstrip('.')
                        
                        # Verificar si es abreviación
                        if palabra_lower in abreviaciones:
                            resultado.append(abreviaciones[palabra_lower])
                        # Capitalizar si no está en lista de excepciones
                        elif palabra_lower not in no_capitalizar or i == 0:
                            # Capitalizar primera letra
                            resultado.append(palabra.capitalize() if i == 0 or not any(c.isdigit() for c in palabra) else palabra)
                        else:
                            resultado.append(palabra.lower())
                    
                    # Reconstruir dirección
                    direccion_normalizada = ' '.join(resultado)
                    
                    # Si no tiene "Argentina" al final, agregarlo (solo si parece una dirección argentina)
                    if 'Argentina' not in direccion_normalizada and 'Buenos Aires' in direccion_normalizada:
                        direccion_normalizada += ', Argentina'
                    
                    print(f"📍 Dirección normalizada: '{destino_texto}' → '{direccion_normalizada}'")
                    return direccion_normalizada
                
                # Normalizar destino
                destino_normalizado = normalizar_direccion(destino_texto)
                
                # Geocodificar destino con Nominatim - con cache
                cache_key_geocode = f'geocode_{destino_normalizado}'
                geocode_data = cache.get(cache_key_geocode)
                if geocode_data is None:
                    try:
                        geocode_resp = requests.get(
                            "https://nominatim.openstreetmap.org/search",
                            params={"q": destino_normalizado, "format": "json", "limit": 1, "countrycodes": "ar"},
                            headers={"User-Agent": "WayGPS-Sofia/1.0"},
                            timeout=8,
                        )
                        geocode_resp.raise_for_status()
                        geocode_data = geocode_resp.json()
                        # Cache por 24 horas para geocodificaciones
                        if geocode_data:
                            cache.set(cache_key_geocode, geocode_data, 86400)
                    except Exception as e:
                        geocode_data = []
                else:
                    print(f"✅ Usando geocodificación desde cache para: {destino_normalizado}")
                
                try:
                    if not geocode_data:
                        return {
                            'texto': f"No pude geocodificar el destino '{destino_texto}'. Probá con un lugar más específico como 'Calle Número, Barrio, Buenos Aires'.",
                            'audio': f"No pude encontrar {destino_texto}. Probá especificando la calle y número, barrio y ciudad."
                        }
                    destino_lat = float(geocode_data[0]["lat"])  # type: ignore
                    destino_lon = float(geocode_data[0]["lon"])  # type: ignore
                    destino_label = geocode_data[0].get("display_name", destino_normalizado)
                except Exception as e:
                    print(f"⚠️ Error geocodificando: {e}")
                    return {
                        'texto': f"No pude ubicar el destino '{destino_texto}'. Intentalo nuevamente con el formato 'Calle Número, Barrio, Buenos Aires'.",
                        'audio': f"No pude ubicar {destino_texto}. Probá con la calle, número y barrio."
                    }
            
            # Verificar que tenemos coordenadas (de zona o geocodificación)
            if not destino_lat or not destino_lon:
                return {
                    'texto': f"No pude ubicar el destino '{destino_texto}'.",
                    'audio': f"No pude ubicar {destino_texto}."
                }
            
            # 4) Calcular ruta y duración con OSRM público - con cache
            cache_key_osrm = f'osrm_{origen_lat}_{origen_lon}_{destino_lat}_{destino_lon}'
            osrm = cache.get(cache_key_osrm)
            if osrm is None:
                try:
                    osrm_url = (
                        f"http://router.project-osrm.org/route/v1/driving/"
                        f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}?overview=false&alternatives=false"
                    )
                    osrm_resp = requests.get(osrm_url, timeout=3)  # Reducido de 8 a 3 segundos
                    osrm_resp.raise_for_status()
                    osrm = osrm_resp.json()
                    # Cache por 1 hora para rutas
                    cache.set(cache_key_osrm, osrm, 3600)
                except Exception:
                    osrm = {}
            else:
                print(f"✅ Usando ruta OSRM desde cache")
            
            try:
                routes = osrm.get("routes") or []
                if not routes:
                    raise ValueError("Sin rutas")
                duration_sec = float(routes[0]["duration"])  # seconds
                distance_m = float(routes[0]["distance"])  # meters
            except Exception:
                # Fallback burdo: distancia geodésica y velocidad estimada 50 km/h
                from math import radians, cos, sin, asin, sqrt
                def haversine(lon1, lat1, lon2, lat2):
                    R = 6371.0
                    dLat = radians(lat2 - lat1)
                    dLon = radians(lon2 - lon1)
                    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                dist_km = haversine(origen_lon, origen_lat, destino_lon, destino_lat)
                est_vel_kmh = float(status.ultima_velocidad_kmh or 50.0) or 50.0
                duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                distance_m = dist_km * 1000.0
            
            # 5) Presentación del ETA
            ahora = datetime.now()
            llegada = ahora + timedelta(seconds=duration_sec)
            horas = int(duration_sec // 3600)
            minutos = int((duration_sec % 3600) // 60)
            dist_km = distance_m / 1000.0
            
            # Texto y audio
            etiqueta_tiempo = []
            if horas:
                etiqueta_tiempo.append(f"{horas} h")
            if minutos or not horas:
                etiqueta_tiempo.append(f"{minutos} min")
            duracion_str = ' '.join(etiqueta_tiempo)
            hora_llegada = llegada.strftime('%H:%M')
            
            texto = (
                f"⏰ Estimado de llegada de *{movil.alias or movil.patente}* a {destino_label}:\n"
                f"• Tiempo: {duracion_str}\n"
                f"• Hora aproximada: {hora_llegada}\n"
                f"• Distancia: {dist_km:.1f} km"
            )
            audio = (
                f"{(movil.alias or movil.patente)} llegaría a {destino_texto} en aproximadamente {duracion_str}. "
                f"Hora estimada {hora_llegada}."
            )
            return {"texto": texto, "audio": audio}
        except Exception as e:
            print(f"Error en calculo de llegada: {e}")
            return {
                'texto': "No pude calcular el tiempo de llegada en este momento.",
                'audio': "No pude calcular el arribo ahora. Intentá en un momento."
            }
    
    def _obtener_cercania(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Encuentra los móviles más cercanos a una ubicación o a otro móvil.
        Retorna el primero y segundo más cercano con distancia y tiempo estimado.
        """
        try:
            texto_completo = variables.get('_texto_completo', '')
            texto_lower = texto_completo.lower()
            consulta_directa_distancia = any(
                frase in texto_lower for frase in [
                    'a cuanto esta', 'a cuánto está',
                    'a que distancia', 'a qué distancia',
                    'cuanto tarda en llegar', 'cuánto tarda en llegar',
                    'cuanto demora en llegar', 'cuánto demora en llegar'
                ]
            )
            destino_texto = variables.get('destino', '')
            destino_es_movil = variables.get('destino_es_movil', False)
            movil_referencia = variables.get('movil_referencia', '')
            movil_referencia = movil_referencia or ''
            movil_referencia = movil_referencia.strip() if movil_referencia else ''
            movil_referencia_contexto = (variables.get('movil') or '').strip()
            
            # NUEVA LÓGICA: Detectar consultas de distancia entre dos entidades
            # Patrones: "que distancia hay/existe entre X y Y"
            patrones_distancia_entre = [
                r'que\s+distancia\s+(?:hay|existe|hay\s+entre|existe\s+entre)\s+entre\s+(.+?)\s+y\s+(.+)',
                r'distancia\s+entre\s+(.+?)\s+y\s+(.+)',
                r'cuanto\s+distancia\s+entre\s+(.+?)\s+y\s+(.+)',
            ]
            
            entidad1 = None
            entidad2 = None
            es_consulta_distancia_entre = False
            
            for patron in patrones_distancia_entre:
                match = re.search(patron, texto_lower, re.IGNORECASE)
                if match:
                    entidad1 = match.group(1).strip()
                    entidad2 = match.group(2).strip()
                    es_consulta_distancia_entre = True
                    print(f"📍 [CERCANIA] Detectada consulta de distancia entre dos entidades: '{entidad1}' y '{entidad2}'")
                    break
            
            # Verificar si es CERCANIA sin destino específico
            texto_lower_check = texto_completo.lower()
            patrones_sin_destino_check = [
                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',  # Sin nada después
                r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca\s*$',  # Sin nada después
                r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?\s*$',  # Sin nada después
            ]
            es_cercania_sin_destino_check = any(re.search(patron, texto_lower_check, re.IGNORECASE) for patron in patrones_sin_destino_check)
            
            # Si es consulta de distancia entre dos entidades, procesarla según los prefijos
            if es_consulta_distancia_entre and entidad1 and entidad2:
                # Identificar prefijos "zona" en las entidades
                tiene_prefijo_zona1 = re.search(r'\b(?:zona|deposito|almacen|base|sede|oficina|planta)\s+', entidad1, re.IGNORECASE)
                tiene_prefijo_zona2 = re.search(r'\b(?:zona|deposito|almacen|base|sede|oficina|planta)\s+', entidad2, re.IGNORECASE)
                
                # Determinar tipo de consulta según prefijos
                if tiene_prefijo_zona1 and tiene_prefijo_zona2:
                    # Ambos tienen prefijo zona: distancia entre zonas
                    print(f"📍 [CERCANIA] Distancia entre zonas: '{entidad1}' y '{entidad2}'")
                    return self._calcular_distancia_zonas(entidad1, entidad2, variables)
                elif tiene_prefijo_zona1 or tiene_prefijo_zona2:
                    # Uno tiene prefijo zona: distancia entre móvil y zona
                    print(f"📍 [CERCANIA] Distancia entre móvil y zona: '{entidad1}' y '{entidad2}'")
                    if tiene_prefijo_zona1:
                        return self._calcular_distancia_movil_zona(entidad2, entidad1, variables)
                    else:
                        return self._calcular_distancia_movil_zona(entidad1, entidad2, variables)
                else:
                    # Ninguno tiene prefijo zona: distancia entre móviles
                    print(f"📍 [CERCANIA] Distancia entre móviles: '{entidad1}' y '{entidad2}'")
                    return self._calcular_distancia_moviles(entidad1, entidad2, variables)
            
            # VERIFICAR PRIMERO: Si hay destino en variables (puede venir del contexto)
            # Si es CERCANIA sin destino específico, USAR el contexto (zona o móvil)
            tiene_destino_de_variables = destino_texto and destino_texto.strip()
            if tiene_destino_de_variables:
                if es_cercania_sin_destino_check:
                    # CERCANIA sin destino específico - USAR destino del contexto
                    print(f"✅ [CERCANIA] CERCANIA sin destino específico - usando destino del contexto: '{destino_texto}'")
                else:
                    print(f"✅ [CERCANIA] Hay destino en variables (del contexto): '{destino_texto}' - NO usando móvil del contexto")
            
            # PRIMERO: Extraer destino del texto si no está en variables
            # Esto debe hacerse ANTES de usar el móvil del contexto
            if not destino_texto:
                # Extraer destino del texto
                t = ''.join(c for c in unicodedata.normalize('NFD', texto_completo.lower()) if unicodedata.category(c) != 'Mn')
                t = t.replace(' al ', ' a el ')
                
                # Separadores para cercanía (con y sin preposiciones)
                separadores = [
                    ' mas cerca de ', ' mas cerca del ', ' mas cerca de la ', ' mas cerca a ',
                    ' mas cercano a ', ' mas cercano de ', ' mas cercano del ',
                    ' mas proximo a ', ' mas proximo de ', ' mas proximo del ',
                    ' mas cerca ', ' mas cercanos ', ' mas cercano ',  # Sin preposición
                    ' mas proximo ', ' mas proximos '  # Sin preposición
                ]
                
                for sep in separadores:
                    if sep in t:
                        destino_texto = t.split(sep)[-1]
                        break
                
                # Patrón específico para "más cercanos a zona X" o "más cercanos a depósito X"
                if not destino_texto:
                    patron_zona = r'mas\s+cercanos?\s+(?:a|de|del|de\s+la)?\s*(?:zona|deposito|almacen|base|sede|oficina|planta)\s+(.+)'
                    match = re.search(patron_zona, t, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        # Incluir la palabra "zona" o "depósito" en el nombre si está presente
                        if 'zona' in t[:match.start()].lower() or 'deposito' in t[:match.start()].lower():
                            # Buscar la palabra completa antes del nombre
                            patron_completo = r'mas\s+cercanos?\s+(?:a|de|del|de\s+la)?\s*((?:zona|deposito|almacen|base|sede|oficina|planta)\s+.+)'
                            match_completo = re.search(patron_completo, t, re.IGNORECASE)
                            if match_completo:
                                destino_texto = match_completo.group(1).strip()
                        else:
                            destino_texto = nombre_zona
                
                # Si no encontró con separadores, buscar patrón "más cercanos X" o "más cercano X"
                if not destino_texto:
                    # Patrón: cualquier palabra + "más cercanos" o "más cercano" + lo que sigue
                    patron_cercania = r'\b(mas|más)\s+(cercanos?|proximos?|cerca)\s+(?:a|de|del|de\s+la)?\s*(.+)$'
                    match = re.search(patron_cercania, t, re.IGNORECASE)
                    if match:
                        destino_texto = match.group(3).strip()
                
                # Si aún no tiene destino, intentar capturar todo después de "más cercanos" (sin preposición)
                if not destino_texto:
                    # Patrón más flexible: "más cercanos" + lo que sigue (puede tener o no preposición)
                    patron_final = r'mas\s+cercanos?\s+(?:a|de|del|de\s+la)?\s*(.+)'
                    match = re.search(patron_final, t, re.IGNORECASE)
                    if match:
                        destino_texto = match.group(1).strip()
                
                # Último intento: buscar patrón "más cercanos" seguido directamente de texto
                if not destino_texto:
                    patron_directo = r'mas\s+cercanos?\s+([a-záéíóúñ0-9\s,]+?)(?:\s+del\s+movil|\s+del\s+vehiculo|\s+del\s+camion|$)'
                    match = re.search(patron_directo, t, re.IGNORECASE)
                    if match:
                        destino_candidato = match.group(1).strip()
                        # Si tiene al menos 3 caracteres y no es solo un artículo/preposición
                        if len(destino_candidato) >= 3 and destino_candidato.lower() not in ['a', 'de', 'del', 'la', 'el', 'al']:
                            destino_texto = destino_candidato
                
                if destino_texto:
                    # Limpiar prefijos comunes
                    prefijos = [
                        'que movil esta ', 'que vehiculo esta ', 'que camion esta ',
                        'cual es el movil ', 'cual es el vehiculo ', 'cual es el camion ',
                        'el movil ', 'el vehiculo ', 'el camion '
                    ]
                    for p in prefijos:
                        if destino_texto.lower().startswith(p):
                            destino_texto = destino_texto[len(p):]
                    
                    destino_texto = destino_texto.strip(' ?!.')
                    print(f"📍 Destino extraído del texto: '{destino_texto}'")
            
            # es_cercania_sin_destino_check ya está definido arriba (línea ~1116)
            # No es necesario redefinirlo aquí
            
            # Si es CERCANIA sin destino pero hay un destino en variables (del contexto de UBICACION_ZONA)
            # ese destino ya fue asignado en views.py, así que NO usar móvil del contexto
            tiene_destino_contexto = (variables.get('destino') or '').strip()
            
            # NUEVA LÓGICA: Si es CERCANIA sin destino específico, usar el contexto (zona o móvil)
            # Si hay destino en variables (zona del contexto), ya está asignado arriba
            # Si no hay destino pero hay móvil del contexto, usarlo como referencia
            if es_cercania_sin_destino_check:
                if tiene_destino_de_variables:
                    # Ya hay destino del contexto (zona) - usar ese
                    print(f"✅ CERCANIA sin destino - usando zona del contexto: '{destino_texto}'")
                elif movil_referencia_contexto and not movil_referencia:
                    # No hay destino pero hay móvil del contexto - usar ese móvil como referencia
                    movil_referencia = movil_referencia_contexto
                    variables['movil_referencia'] = movil_referencia_contexto
                    print(f"✅ CERCANIA sin destino - usando móvil del contexto: '{movil_referencia_contexto}'")
                else:
                    # Sin contexto - se mostrarán móviles más cercanos entre sí
                    print(f"ℹ️ CERCANIA sin destino y sin contexto - mostrando móviles más cercanos entre sí")
            elif not destino_texto and not movil_referencia and movil_referencia_contexto:
                # No es CERCANIA sin destino - usar móvil del contexto solo si no hay destino
                if tiene_destino_de_variables:
                    print(f"✅ Ya hay destino en variables ({destino_texto}), NO usando móvil como destino")
                elif tiene_destino_contexto:
                    print(f"✅ Hay destino del contexto ({tiene_destino_contexto}), NO usando móvil como destino")
                else:
                    # Usar móvil del contexto como destino
                    movil_referencia = movil_referencia_contexto
                    variables['movil_referencia'] = movil_referencia_contexto
                    print(f"⚠️ Usando móvil del contexto como destino: '{movil_referencia_contexto}'")

            # 1) Determinar destino: ubicación o móvil de referencia
            destino_lat = None
            destino_lon = None
            destino_label = None
            destino_label_es_movil = False
            es_movil_referencia = False
            movil_ref = None
            movil_destino_obj = None
            movil_origen_obj = None
            
            # Primero verificar si es un móvil de referencia
            if destino_es_movil and destino_texto:
                movil_destino_obj = Movil.objects.filter(
                    Q(patente__iexact=destino_texto) |
                    Q(alias__iexact=destino_texto) |
                    Q(codigo__iexact=destino_texto)
                ).first()
                if movil_destino_obj:
                    status_destino = MovilStatus.objects.filter(movil=movil_destino_obj).only('ultimo_lat', 'ultimo_lon').first()
                    if status_destino and status_destino.ultimo_lat and status_destino.ultimo_lon:
                        destino_lat = float(status_destino.ultimo_lat)
                        destino_lon = float(status_destino.ultimo_lon)
                        destino_label = movil_destino_obj.alias or movil_destino_obj.patente
                        destino_label_es_movil = True
                        destino_texto = ''
                    else:
                        return {
                            'texto': f"El móvil '{destino_texto}' no tiene posición actual para calcular la cercanía.",
                            'audio': f"No puedo calcular la cercanía porque {destino_texto} no tiene posición actual."
                        }

            # Determinar móvil de referencia (origen) independientemente del tipo
            movil_origen_codigo = movil_referencia or (variables.get('movil') or '').strip()
            if movil_origen_codigo:
                movil_origen_obj = Movil.objects.filter(
                    Q(patente__iexact=movil_origen_codigo) |
                    Q(alias__iexact=movil_origen_codigo) |
                    Q(codigo__iexact=movil_origen_codigo)
                ).first()

            # IMPORTANTE: NO usar móvil como destino si:
            # - Ya hay destino_texto (puede venir del contexto)
            # - Es CERCANIA sin destino específico (mostrar móviles más cercanos entre sí)
            if movil_referencia and not destino_es_movil and not destino_texto and not consulta_directa_distancia and not tiene_destino_de_variables and not es_cercania_sin_destino_check:
                # Buscar móvil de referencia
                movil_ref = Movil.objects.filter(
                    Q(patente__icontains=movil_referencia.upper()) |
                    Q(alias__icontains=movil_referencia.upper()) |
                    Q(codigo__icontains=movil_referencia.upper())
                ).first()
                
                if movil_ref:
                    status_ref = MovilStatus.objects.filter(movil=movil_ref).only('ultimo_lat', 'ultimo_lon').first()
                    if status_ref and status_ref.ultimo_lat and status_ref.ultimo_lon:
                        destino_lat = float(status_ref.ultimo_lat)
                        destino_lon = float(status_ref.ultimo_lon)
                        destino_label = f"{movil_ref.alias or movil_ref.patente}"
                        destino_label_es_movil = True
                        es_movil_referencia = True
                        print(f"📍 Usando móvil de referencia como destino: '{destino_label}'")
                    else:
                        return {
                            'texto': f"El móvil de referencia '{movil_ref.alias or movil_ref.patente}' no tiene posición actual.",
                            'audio': f"No puedo usar {movil_ref.alias or movil_ref.patente} como referencia. No tiene posición."
                        }
                else:
                    return {
                        'texto': f"No encontré el móvil de referencia '{movil_referencia}'.",
                        'audio': f"No encontré el móvil de referencia {movil_referencia}."
                    }
            elif movil_referencia and tiene_destino_de_variables:
                print(f"⚠️ Hay móvil de referencia '{movil_referencia}' pero también hay destino del contexto '{destino_texto}' - NO usando móvil como destino")

            # Caso específico: distancia entre dos móviles
            if destino_es_movil and movil_destino_obj and movil_origen_obj:
                if movil_destino_obj.id == movil_origen_obj.id:
                    return {
                        'texto': "Necesito dos móviles distintos para comparar la distancia.",
                        'audio': "Decime dos vehículos distintos para calcular la distancia."
                    }

                status_origen = MovilStatus.objects.filter(movil=movil_origen_obj).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh').first()
                if not status_origen or not status_origen.ultimo_lat or not status_origen.ultimo_lon:
                    return {
                        'texto': f"El móvil '{movil_origen_obj.alias or movil_origen_obj.patente}' no tiene posición actual para calcular la distancia.",
                        'audio': f"No puedo usar {movil_origen_obj.alias or movil_origen_obj.patente} porque no tiene posición actual."
                    }

                origen_lat = float(status_origen.ultimo_lat)
                origen_lon = float(status_origen.ultimo_lon)

                # Calcular distancia y tiempo entre los dos móviles - con cache
                cache_key_osrm = f'osrm_{origen_lat}_{origen_lon}_{destino_lat}_{destino_lon}'
                osrm = cache.get(cache_key_osrm)
                if osrm is None:
                    try:
                        osrm_url = (
                            f"http://router.project-osrm.org/route/v1/driving/"
                            f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}?overview=false&alternatives=false"
                        )
                        osrm_resp = requests.get(osrm_url, timeout=3)  # Reducido de 5 a 3 segundos
                        osrm_resp.raise_for_status()
                        osrm = osrm_resp.json()
                        cache.set(cache_key_osrm, osrm, 3600)  # 1 hora
                    except Exception:
                        osrm = {}
                else:
                    print(f"✅ Usando ruta OSRM desde cache (móvil-móvil)")
                
                try:
                    routes = osrm.get("routes") or []
                    if routes:
                        duration_sec = float(routes[0]["duration"])
                        distance_m = float(routes[0]["distance"])
                    else:
                        raise ValueError("Sin rutas")
                except Exception:
                    def haversine(lon1, lat1, lon2, lat2):
                        R = 6371.0
                        dLat = radians(lat2 - lat1)
                        dLon = radians(lon2 - lon1)
                        a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                        c = 2 * asin(sqrt(a))
                        return R * c
                    dist_km = haversine(origen_lon, origen_lat, destino_lon, destino_lat)
                    est_vel_kmh = float(status_origen.ultima_velocidad_kmh or 50.0) or 50.0
                    duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                    distance_m = dist_km * 1000.0

                distancia_km = distance_m / 1000.0
                duracion_min = duration_sec / 60.0

                origen_label = movil_origen_obj.alias or movil_origen_obj.patente
                destino_label = destino_label or (movil_destino_obj.alias or movil_destino_obj.patente)

                texto_respuesta = (
                    f"📍 Distancia entre *{origen_label}* y *{destino_label}*:\n"
                    f"• Distancia: {distancia_km:.1f} km\n"
                    f"• Tiempo estimado: {int(duracion_min)} min"
                )
                audio_respuesta = (
                    f"La distancia entre {origen_label} y {destino_label} es de {distancia_km:.1f} kilómetros, "
                    f"con un tiempo estimado de {int(duracion_min)} minutos."
                )
                return {
                    'texto': texto_respuesta,
                    'audio': audio_respuesta
                }
            
            # Si no es móvil de referencia, procesar destino_texto extraído arriba
            if not destino_lat or not destino_lon:
                if destino_texto:
                    # PRIMERO: Verificar si contiene palabras de zona (zona, depósito, etc.)
                    # Si contiene estas palabras, NO intentar buscar como móvil
                    tiene_palabra_zona = re.search(r'\b(?:zona|deposito|almacen|base|sede|oficina|planta)\b', destino_texto, re.IGNORECASE)
                    
                    # Verificar si es un móvil de referencia SOLO si NO tiene palabra de zona
                    if not tiene_palabra_zona and len(destino_texto.strip().split()) <= 2:
                        # Intentar extraer patente o nombre de móvil
                        patron_movil = r'\b([A-Za-z]{2,4}\s*\d{2,4}|[a-zA-Z]+\s*\d+)\b'
                        match = re.search(patron_movil, destino_texto, re.IGNORECASE)
                        if match:
                            posible_movil_ref = match.group(1).replace(' ', '').upper()
                            # Reintentar como móvil de referencia
                            movil_ref_temp = Movil.objects.filter(
                                Q(patente__icontains=posible_movil_ref) |
                                Q(alias__icontains=posible_movil_ref) |
                                Q(codigo__icontains=posible_movil_ref)
                            ).first()
                            if movil_ref_temp:
                                status_ref = MovilStatus.objects.filter(movil=movil_ref_temp).first()
                                if status_ref and status_ref.ultimo_lat and status_ref.ultimo_lon:
                                    destino_lat = float(status_ref.ultimo_lat)
                                    destino_lon = float(status_ref.ultimo_lon)
                                    destino_label = f"{movil_ref_temp.alias or movil_ref_temp.patente}"
                                    destino_label_es_movil = True
                                    es_movil_referencia = True
                                    movil_ref = movil_ref_temp
                                    destino_texto = ''  # Ya tenemos destino, limpiar texto
                    
                    if destino_texto:
                        destino_label = destino_texto
                        destino_label_es_movil = False
                
                # Inicializar skip_geocode
                skip_geocode = False
                
                # Si aún no tenemos destino, buscar primero en zonas antes de geocodificar
                if not destino_lat or not destino_lon:
                    # PRIMERO: Si hay destino_texto, buscar en zonas ANTES de verificar si es sin destino
                    if destino_texto:
                        try:
                            usuario_consulta = variables.get('_usuario')
                            zona_encontrada = self._buscar_zona_por_nombre(destino_texto, usuario_consulta)
                            
                            if zona_encontrada:
                                zona, destino_lat, destino_lon, destino_label = zona_encontrada
                                print(f"📍 Usando zona encontrada para cercanía: '{zona.nombre}' ({destino_lat}, {destino_lon})")
                                # Para cercanía, solo usar el nombre de la zona (sin dirección)
                                destino_label = zona.nombre
                                destino_label_es_movil = False
                                skip_geocode = True
                        except Exception as e:
                            print(f"⚠️ Error buscando zona para cercanía: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # SEGUNDO: Si aún no tenemos destino, verificar si es CERCANIA sin destino específico
                    if not destino_lat or not destino_lon:
                        if not destino_texto:
                            # Caso especial: CERCANIA sin destino específico - mostrar móviles más cercanos entre sí
                            texto_lower = texto_completo.lower()
                            patrones_sin_destino = [
                                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?',
                                r'qu[eé]\s+m[oó]viles?\s+est[aá]n?\s+m[aá]s\s+cerca',
                                r'm[oó]viles?\s+m[aá]s\s+cercan[oa]s?',
                            ]
                            es_sin_destino = any(re.search(patron, texto_lower, re.IGNORECASE) for patron in patrones_sin_destino)
                            
                            if es_sin_destino:
                                # Mostrar los móviles más cercanos entre sí
                                print("📍 Consulta de CERCANIA sin destino - mostrando móviles más cercanos entre sí")
                                # Calcular distancias entre todos los móviles
                                # Optimizar: usar prefetch_related para status (OneToOne)
                                moviles_activos = Movil.objects.filter(activo=True).prefetch_related('status').only('id', 'patente', 'alias', 'codigo')
                                pares_cercanos = []
                                
                                moviles_con_posicion = []
                                for movil in moviles_activos:
                                    # Acceder al status precargado
                                    status = getattr(movil, 'status', None)
                                    if status and status.ultimo_lat and status.ultimo_lon:
                                        moviles_con_posicion.append({
                                            'movil': movil,
                                            'lat': float(status.ultimo_lat),
                                            'lon': float(status.ultimo_lon),
                                            'alias': movil.alias or movil.patente
                                        })
                                
                                # Calcular distancias entre todos los pares
                                for i, movil1 in enumerate(moviles_con_posicion):
                                    for movil2 in moviles_con_posicion[i+1:]:
                                        # Usar OSRM para calcular distancia - con cache
                                        cache_key_osrm = f'osrm_{movil1["lat"]}_{movil1["lon"]}_{movil2["lat"]}_{movil2["lon"]}'
                                        osrm = cache.get(cache_key_osrm)
                                        if osrm is None:
                                            try:
                                                osrm_url = (
                                                    f"http://router.project-osrm.org/route/v1/driving/"
                                                    f"{movil1['lon']},{movil1['lat']};{movil2['lon']},{movil2['lat']}?overview=false&alternatives=false"
                                                )
                                                osrm_resp = requests.get(osrm_url, timeout=3)  # Reducido de 5 a 3 segundos
                                                osrm_resp.raise_for_status()
                                                osrm = osrm_resp.json()
                                                cache.set(cache_key_osrm, osrm, 3600)  # 1 hora
                                            except Exception:
                                                osrm = {}
                                        
                                        try:
                                            routes = osrm.get("routes") or []
                                            if routes:
                                                distance_m = float(routes[0]["distance"])
                                                duration_sec = float(routes[0]["duration"])
                                            else:
                                                raise ValueError("Sin rutas")
                                        except Exception:
                                            # Fallback: distancia geodésica
                                            def haversine(lon1, lat1, lon2, lat2):
                                                R = 6371.0
                                                dLat = radians(lat2 - lat1)
                                                dLon = radians(lon2 - lon1)
                                                a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                                                c = 2 * asin(sqrt(a))
                                                return R * c
                                            dist_km = haversine(movil1['lon'], movil1['lat'], movil2['lon'], movil2['lat'])
                                            distance_m = dist_km * 1000.0
                                            duration_sec = (dist_km / 50.0) * 3600.0
                                        
                                        pares_cercanos.append({
                                            'movil1': movil1,
                                            'movil2': movil2,
                                            'distance_m': distance_m,
                                            'duration_sec': duration_sec
                                        })
                                
                                if not pares_cercanos:
                                    return {
                                        'texto': "No hay suficientes móviles con posición para calcular cercanía.",
                                        'audio': "No hay suficientes móviles disponibles."
                                    }
                                
                                # Ordenar por distancia y tomar los 2 pares más cercanos
                                pares_cercanos.sort(key=lambda x: x['distance_m'])
                                top_2_pares = pares_cercanos[:2]
                                
                                texto_respuesta = "📍 Móviles más cercanos entre sí:\n\n"
                                audio_respuesta = "Los móviles más cercanos son: "
                                
                                for i, par in enumerate(top_2_pares, 1):
                                    distancia_km = par['distance_m'] / 1000.0
                                    duracion_min = par['duration_sec'] / 60.0
                                    
                                    texto_respuesta += f"{i}. *{par['movil1']['alias']}* y *{par['movil2']['alias']}*\n"
                                    texto_respuesta += f"   • Distancia: {distancia_km:.1f} km\n"
                                    texto_respuesta += f"   • Tiempo estimado: {int(duracion_min)} min\n\n"
                                    
                                    if i == 1:
                                        audio_respuesta += f"{par['movil1']['alias']} y {par['movil2']['alias']} a {distancia_km:.1f} kilómetros, "
                                    elif i == 2:
                                        audio_respuesta += f"y {par['movil1']['alias']} y {par['movil2']['alias']} a {distancia_km:.1f} kilómetros."
                                
                                return {
                                    'texto': texto_respuesta.strip(),
                                    'audio': audio_respuesta
                                }
                        else:
                            return {
                                'texto': "No pude identificar el destino. Por ejemplo: 'qué móvil está más cerca de Rosario' o 'qué móvil está más cerca del camión 2'.",
                                'audio': "Decime a dónde o a qué móvil querés buscar cercanía."
                            }
                else:
                    skip_geocode = True  # Ya tenemos destino (móvil)
                
                # Normalizar dirección (reutilizar función de _calcular_llegada) solo si no se encontró zona
                if not skip_geocode:
                    def normalizar_direccion(direccion):
                        no_capitalizar = {'de', 'del', 'y', 'la', 'el', 'las', 'los', 'en', 'por', 'para', 'con', 'sin', 'al', 'a'}
                        abreviaciones = {
                            'av': 'Avenida', 'av.': 'Avenida', 'avda': 'Avenida', 'avda.': 'Avenida',
                            'blv': 'Boulevard', 'blvr': 'Boulevard', 'blvr.': 'Boulevard',
                            'caba': 'Buenos Aires', 'bs as': 'Buenos Aires', 'cap': 'Buenos Aires', 'cap fed': 'Buenos Aires',
                        }
                        palabras = direccion.split()
                        resultado = []
                        for i, palabra in enumerate(palabras):
                            palabra_lower = palabra.lower().rstrip(',').rstrip('.')
                            if palabra_lower in abreviaciones:
                                resultado.append(abreviaciones[palabra_lower])
                            elif palabra_lower not in no_capitalizar or i == 0:
                                resultado.append(palabra.capitalize() if i == 0 or not any(c.isdigit() for c in palabra) else palabra)
                            else:
                                resultado.append(palabra.lower())
                        direccion_normalizada = ' '.join(resultado)
                        if 'Argentina' not in direccion_normalizada and 'Buenos Aires' in direccion_normalizada:
                            direccion_normalizada += ', Argentina'
                        return direccion_normalizada
                    
                    destino_normalizado = normalizar_direccion(destino_texto)
                    destino_label = destino_normalizado
                    destino_label_es_movil = False
                    
                    # Geocodificar destino con Nominatim
                    try:
                        geocode_resp = requests.get(
                            "https://nominatim.openstreetmap.org/search",
                            params={"q": destino_normalizado, "format": "json", "limit": 1, "countrycodes": "ar"},
                            headers={"User-Agent": "WayGPS-Sofia/1.0"},
                            timeout=8,
                        )
                        geocode_resp.raise_for_status()
                        geocode_data = geocode_resp.json()
                        if not geocode_data:
                            return {
                                'texto': f"No pude geocodificar el destino '{destino_texto}'. Probá con un lugar más específico.",
                                'audio': f"No pude encontrar {destino_texto}. Decime un lugar más específico."
                            }
                        destino_lat = float(geocode_data[0]["lat"])
                        destino_lon = float(geocode_data[0]["lon"])
                        destino_label = geocode_data[0].get("display_name", destino_normalizado)
                        destino_label_es_movil = False
                    except Exception as e:
                        print(f"⚠️ Error geocodificando: {e}")
                        return {
                            'texto': f"No pude ubicar el destino '{destino_texto}'. Intentalo nuevamente.",
                            'audio': f"No pude ubicar {destino_texto}. Intentá nuevamente."
                        }

            # Caso: distancia directa entre un móvil (origen) y un destino geográfico
            if consulta_directa_distancia and destino_lat and destino_lon and movil_origen_obj:
                status_origen = MovilStatus.objects.filter(movil=movil_origen_obj).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh').first()
                if not status_origen or not status_origen.ultimo_lat or not status_origen.ultimo_lon:
                    return {
                        'texto': f"El móvil '{movil_origen_obj.alias or movil_origen_obj.patente}' no tiene posición actual para calcular la distancia.",
                        'audio': f"No puedo usar {movil_origen_obj.alias or movil_origen_obj.patente} porque no tiene posición actual."
                    }

                origen_lat = float(status_origen.ultimo_lat)
                origen_lon = float(status_origen.ultimo_lon)

                # Calcular con OSRM - con cache
                cache_key_osrm = f'osrm_{origen_lat}_{origen_lon}_{destino_lat}_{destino_lon}'
                osrm = cache.get(cache_key_osrm)
                if osrm is None:
                    try:
                        osrm_url = (
                            f"http://router.project-osrm.org/route/v1/driving/"
                            f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}?overview=false&alternatives=false"
                        )
                        osrm_resp = requests.get(osrm_url, timeout=3)  # Reducido de 5 a 3 segundos
                        osrm_resp.raise_for_status()
                        osrm = osrm_resp.json()
                        cache.set(cache_key_osrm, osrm, 3600)  # 1 hora
                    except Exception:
                        osrm = {}
                
                try:
                    routes = osrm.get("routes") or []
                    if routes:
                        duration_sec = float(routes[0]["duration"])
                        distance_m = float(routes[0]["distance"])
                    else:
                        raise ValueError("Sin rutas")
                except Exception:
                    def haversine(lon1, lat1, lon2, lat2):
                        R = 6371.0
                        dLat = radians(lat2 - lat1)
                        dLon = radians(lon2 - lon1)
                        a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                        c = 2 * asin(sqrt(a))
                        return R * c
                    dist_km = haversine(origen_lon, origen_lat, destino_lon, destino_lat)
                    est_vel_kmh = float(status_origen.ultima_velocidad_kmh or 50.0) or 50.0
                    duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                    distance_m = dist_km * 1000.0

                distancia_km = distance_m / 1000.0
                duracion_min = duration_sec / 60.0
                origen_label = movil_origen_obj.alias or movil_origen_obj.patente
                destino_label_simple = destino_label or destino_texto

                texto_respuesta = (
                    f"📍 Distancia entre *{origen_label}* y *{destino_label_simple}*:\n"
                    f"• Distancia: {distancia_km:.1f} km\n"
                    f"• Tiempo estimado: {int(duracion_min)} min"
                )
                audio_respuesta = (
                    f"{origen_label} está a {distancia_km:.1f} kilómetros de {destino_label_simple}, "
                    f"con un tiempo estimado de {int(duracion_min)} minutos."
                )
                return {
                    'texto': texto_respuesta,
                    'audio': audio_respuesta
                }
            
            # 2) Obtener todos los móviles activos con posición - optimizado
            moviles_activos = Movil.objects.filter(activo=True).prefetch_related('status').only('id', 'patente', 'alias', 'codigo')
            resultados_cercania = []
            
            for movil in moviles_activos:
                # Acceder al status precargado
                status = getattr(movil, 'status', None)
                if not status or not status.ultimo_lat or not status.ultimo_lon:
                    continue
                
                # Si es móvil de referencia, excluirlo de los resultados
                if es_movil_referencia and movil_ref and movil.id == movil_ref.id:
                    continue
                
                origen_lat = float(status.ultimo_lat)
                origen_lon = float(status.ultimo_lon)
                
                # 3) Calcular distancia y tiempo con OSRM
                # Calcular con OSRM - con cache
                cache_key_osrm = f'osrm_{origen_lat}_{origen_lon}_{destino_lat}_{destino_lon}'
                osrm = cache.get(cache_key_osrm)
                if osrm is None:
                    try:
                        osrm_url = (
                            f"http://router.project-osrm.org/route/v1/driving/"
                            f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}?overview=false&alternatives=false"
                        )
                        osrm_resp = requests.get(osrm_url, timeout=3)  # Reducido de 5 a 3 segundos
                        osrm_resp.raise_for_status()
                        osrm = osrm_resp.json()
                        cache.set(cache_key_osrm, osrm, 3600)  # 1 hora
                    except Exception:
                        osrm = {}
                
                try:
                    routes = osrm.get("routes") or []
                    if routes:
                        duration_sec = float(routes[0]["duration"])
                        distance_m = float(routes[0]["distance"])
                    else:
                        raise ValueError("Sin rutas")
                except Exception:
                    # Fallback: distancia geodésica
                    def haversine(lon1, lat1, lon2, lat2):
                        R = 6371.0
                        dLat = radians(lat2 - lat1)
                        dLon = radians(lon2 - lon1)
                        a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                        c = 2 * asin(sqrt(a))
                        return R * c
                    dist_km = haversine(origen_lon, origen_lat, destino_lon, destino_lat)
                    est_vel_kmh = float(status.ultima_velocidad_kmh or 50.0) or 50.0
                    duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                    distance_m = dist_km * 1000.0
                
                resultados_cercania.append({
                    'movil': movil,
                    'alias': movil.alias or movil.patente,
                    'distance_m': distance_m,
                    'duration_sec': duration_sec
                })
            
            # 4) Ordenar por distancia y tomar top 2
            if not resultados_cercania:
                return {
                    'texto': "No hay móviles activos con posición para calcular cercanía.",
                    'audio': "No hay móviles disponibles para buscar cercanía."
                }
            
            resultados_cercania.sort(key=lambda x: x['distance_m'])
            top_2 = resultados_cercania[:2]
            
            # 5) Formatear respuesta
            if es_movil_referencia:
                texto_respuesta = f"📍 Móviles más cercanos a *{destino_label}*:\n\n"
                audio_respuesta = f"Los móviles más cercanos a {destino_label} son: "
            else:
                texto_respuesta = f"📍 Móviles más cercanos a *{destino_label}*:\n\n"
                audio_respuesta = f"Los móviles más cercanos a {destino_label} son: "
            
            for i, resultado in enumerate(top_2, 1):
                movil = resultado['movil']
                distancia_km = resultado['distance_m'] / 1000.0
                duracion_min = resultado['duration_sec'] / 60.0
                
                texto_respuesta += f"{i}. *{movil.alias or movil.patente}*\n"
                texto_respuesta += f"   • Distancia: {distancia_km:.1f} km\n"
                texto_respuesta += f"   • Tiempo estimado: {int(duracion_min)} min\n\n"
                
                if i == 1:
                    audio_respuesta += f"{movil.alias or movil.patente} a {distancia_km:.1f} kilómetros, "
                elif i == 2:
                    audio_respuesta += f"y {movil.alias or movil.patente} a {distancia_km:.1f} kilómetros."
            
            return {
                'texto': texto_respuesta.strip(),
                'audio': audio_respuesta
            }
            
        except Exception as e:
            print(f"❌ Error en cercanía: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "No pude calcular la cercanía en este momento.",
                'audio': "No pude buscar los móviles más cercanos ahora. Intentá en un momento."
            }
    
    def _responder_saludo(self) -> str:
        """Responde saludos"""
        saludos = [
            {
                'texto': "¡Hola! Soy Sofia, tu asistente de GPS. ¿En qué puedo ayudarte?",
                'audio': "¡Hola! Soy Sofia, tu asistente de GPS. ¿En qué puedo ayudarte?"
            },
            {
                'texto': "¡Hola! Estoy lista para ayudarte con tus vehículos. ¿Qué necesitas?",
                'audio': "¡Hola! Estoy lista para ayudarte con tus vehículos. ¿Qué necesitas?"
            },
            {
                'texto': "¡Hola! Soy Sofia. Puedo contarte dónde están tus móviles, sus recorridos y mucho más.",
                'audio': "¡Hola! Soy Sofia. Puedo contarte dónde están tus móviles y sus recorridos."
            },
        ]
        import random
        return random.choice(saludos)
    
    def _obtener_ubicacion_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Obtiene la ubicación/dirección de una zona específica.
        """
        try:
            texto_completo = variables.get('_texto_completo', '')
            nombre_zona = variables.get('zona', '') or variables.get('destino', '')
            
            # Si no hay nombre de zona en variables, intentar extraerlo del texto
            if not nombre_zona:
                # Limpiar el texto de palabras comunes de consulta
                texto_limpio = texto_completo.lower()
                palabras_consulta = ['donde', 'ubicacion', 'ubicación', 'direccion', 'dirección', 'domicilio', 
                                    'esta', 'está', 'queda', 'queda', 'se encuentra', 'se ubica', 'la zona']
                for palabra in palabras_consulta:
                    texto_limpio = texto_limpio.replace(palabra, '')
                nombre_zona = texto_limpio.strip()
            
            if not nombre_zona:
                return {
                    'texto': "No especificaste qué zona querés consultar. Por ejemplo: '¿dónde está depósito 3?' o '¿cuál es la dirección de zona norte?'",
                    'audio': "Decime qué zona querés consultar."
                }
            
            # Buscar la zona
            usuario_consulta = variables.get('_usuario')
            zona_encontrada = self._buscar_zona_por_nombre(nombre_zona, usuario_consulta)
            
            if not zona_encontrada:
                return {
                    'texto': f"No encontré una zona llamada '{nombre_zona}'. Verificá el nombre e intentá nuevamente.",
                    'audio': f"No encontré la zona {nombre_zona}. Verificá el nombre."
                }
            
            zona, latitud, longitud, _ = zona_encontrada
            
            # IMPORTANTE: Actualizar el nombre de la zona en variables con el nombre real/normalizado de la BD
            # Esto asegura que se guarde correctamente en el contexto para futuras consultas
            variables['zona'] = zona.nombre
            variables['destino'] = zona.nombre  # También guardar como destino para CERCANIA/LLEGADA
            print(f"📍 [UBICACION_ZONA] Guardando nombre real de zona en variables: '{zona.nombre}'")
            
            # Construir respuesta con la información de la zona
            texto = f"📍 *{zona.nombre}*\n\n"
            audio_parts = [f"La zona {zona.nombre}"]
            
            if zona.direccion_formateada:
                texto += f"📍 Dirección: {zona.direccion_formateada}\n"
                audio_parts.append(f"está ubicada en {zona.direccion_formateada}")
            elif zona.direccion:
                texto += f"📍 Dirección: {zona.direccion}\n"
                audio_parts.append(f"está ubicada en {zona.direccion}")
            else:
                texto += f"📍 Coordenadas: {latitud:.6f}, {longitud:.6f}\n"
                audio_parts.append(f"está en las coordenadas {latitud:.4f}, {longitud:.4f}")
            
            if zona.descripcion:
                texto += f"📝 Descripción: {zona.descripcion}\n"
            
            # Obtener el display del tipo
            tipo_display = dict(zona.ZonaTipo.choices).get(zona.tipo, zona.tipo)
            texto += f"🗺️ Tipo: {tipo_display}"
            
            audio = ". ".join(audio_parts) + "."
            
            return {
                'texto': texto,
                'audio': audio
            }
            
        except Exception as e:
            print(f"Error obteniendo ubicación de zona: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al consultar la ubicación de la zona.",
                'audio': "No pude consultar la ubicación de la zona. Intentá nuevamente."
            }

    def _listar_activos(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Lista los móviles activos (reportando en las últimas 24hs).
        """
        try:
            # Definir límite de tiempo (24 horas)
            limite = timezone.now() - timedelta(hours=24)
            
            # Consultar móviles activos con reporte reciente
            # Usamos select_related para optimizar queries
            # Nota: movil__geocode es OneToOne, así que select_related funciona bien
            moviles_activos = MovilStatus.objects.filter(
                fecha_gps__gte=limite
            ).select_related('movil', 'movil__geocode').order_by('-fecha_gps')
            
            cantidad = moviles_activos.count()
            
            if cantidad == 0:
                return {
                    'texto': "No hay móviles activos reportando en las últimas 24 horas.",
                    'audio': "No detecto ningún móvil activo en las últimas 24 horas."
                }
            
            # Construir respuesta
            texto = f"📋 *Móviles Activos ({cantidad})*\n\n"
            audio_parts = [f"Hay {cantidad} móviles activos."]
            
            # Listar detalles (limitado a 10 para no saturar)
            for status in moviles_activos[:10]:
                try:
                    movil = status.movil
                    nombre = movil.alias or movil.patente or "Sin nombre"
                    
                    # Formatear hora de forma segura
                    if status.fecha_gps:
                        hora = status.fecha_gps.strftime('%H:%M')
                    else:
                        hora = "N/A"
                    
                    # Intentar obtener ubicación breve
                    ubicacion = ""
                    try:
                        # Usar prefetch_related o acceso directo más seguro
                        if hasattr(movil, 'geocode'):
                            try:
                                geocode = movil.geocode
                                if geocode:
                                    # Priorizar: Localidad > Barrio > Partido > Provincia
                                    loc = geocode.localidad
                                    barrio = geocode.barrio
                                    
                                    if loc and barrio:
                                        ubicacion = f"{barrio}, {loc}"
                                    elif loc:
                                        ubicacion = loc
                                    elif barrio:
                                        ubicacion = barrio
                                    else:
                                        ubicacion = geocode.provincia or ""
                            except Exception as e:
                                print(f"Error accediendo geocode para {nombre}: {e}")
                                pass
                    except Exception as e:
                        print(f"Error procesando ubicación para {nombre}: {e}")
                        pass
                    
                    if ubicacion:
                        texto += f"• *{nombre}*: {hora} hs ({ubicacion})\n"
                    else:
                        texto += f"• *{nombre}*: {hora} hs\n"
                except Exception as e:
                    print(f"Error procesando móvil en listado: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if cantidad > 10:
                texto += f"\n... y {cantidad - 10} más."
            
            # Audio resumen detallado
            audio = f"Hay {cantidad} móviles activos. "
            
            # Limitar audio a los primeros 5 para no hacerlo eterno
            detalles_audio = []
            for status in moviles_activos[:5]:
                try:
                    movil = status.movil
                    nombre = movil.alias or movil.patente or "Sin nombre"
                    
                    # Obtener ubicación para audio
                    ubic_audio = "ubicación desconocida"
                    try:
                        if hasattr(movil, 'geocode'):
                            try:
                                geocode = movil.geocode
                                if geocode:
                                    # Para audio solo localidad o barrio
                                    ubic_audio = geocode.localidad or geocode.barrio or "zona desconocida"
                            except Exception:
                                pass
                    except Exception:
                        pass
                    
                    detalles_audio.append(f"{nombre} en {ubic_audio}")
                except Exception as e:
                    print(f"Error procesando móvil para audio: {e}")
                    continue
            
            audio += ", ".join(detalles_audio) + "."
            
            if cantidad > 5:
                audio += f" y {cantidad - 5} más."
                
            return {
                'texto': texto,
                'audio': audio
            }
            
        except Exception as e:
            print(f"Error listando activos: {e}")
            return {
                'texto': "Error al consultar móviles activos.",
                'audio': "Tuve un problema consultando la lista de activos."
            }

    def _situacion_flota(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Reporte de situación de flota: Estado (Movimiento/Detenido) y Ubicación.
        """
        try:
            from zonas.models import Zona  # Importar aquí para evitar problemas circulares
            limite = timezone.now() - timedelta(hours=24)
            moviles_status = MovilStatus.objects.filter(
                fecha_gps__gte=limite
            ).select_related('movil').order_by('movil__alias')
            
            if not moviles_status.exists():
                return {
                    'texto': "No hay información reciente de la flota (últimas 24hs).",
                    'audio': "No tengo información reciente de la flota."
                }
            
            texto = "🚦 *Situación de Flota*\n\n"
            detenidos = 0
            circulando = 0
            detalles_audio = []
            
            # Intentar importar Posicion, si falla usar solo datos de status
            Posicion = None
            try:
                from gps.models import Posicion
            except ImportError:
                print("⚠️ No se pudo importar modelo Posicion, usando estimación simple")
            
            for status in moviles_status:
                movil = status.movil
                nombre = movil.alias or movil.patente
                
                # 1. Determinar Estado (Circulando vs Detenido)
                # Criterio estricto: Últimos 5 reportes con velocidad > 0
                estado_str = "Detenido"
                icono = "🛑"
                
                # Verificación rápida primero
                if status.ultima_velocidad_kmh and status.ultima_velocidad_kmh > 5:
                    # Si tenemos Posicion, hacer verificación histórica
                    if Posicion:
                        try:
                            # Traer últimas 5 posiciones
                            ultimas_pos = Posicion.objects.filter(movil=movil).order_by('-fecha_gps')[:5]
                            if len(ultimas_pos) >= 3: # Al menos 3 para evaluar
                                # Si la mayoría tiene velocidad > 0
                                con_velocidad = sum(1 for p in ultimas_pos if (p.velocidad or 0) > 0)
                                if con_velocidad >= 3:
                                    estado_str = "Circulando"
                                    icono = "🚗" # Icono de movimiento
                                    circulando += 1
                                else:
                                    detenidos += 1
                            else:
                                # Pocos datos, confiar en el último
                                estado_str = "En Movimiento"
                                icono = "🚗"
                                circulando += 1
                        except Exception as e:
                            print(f"Error consultando posiciones para {nombre}: {e}")
                            # Fallback a dato simple
                            estado_str = "En Movimiento"
                            icono = "🚗"
                            circulando += 1
                    else:
                        # Sin modelo Posicion, confiar en el último status
                        estado_str = "En Movimiento"
                        icono = "🚗"
                        circulando += 1
                else:
                    detenidos += 1
                
                # 2. Determinar Ubicación (Zona > Localidad)
                ubicacion_str = "Ubicación desconocida"
                
                # Chequear si está en zona (Geofence check simple)
                # Esto puede ser costoso si hay muchas zonas. 
                # Idealmente usaríamos PostGIS: Zona.objects.filter(geom__contains=punto)
                zona_nombre = None
                if status.ultimo_lat and status.ultimo_lon:
                    try:
                        from django.contrib.gis.geos import Point
                        # Asegurar que lat/lon son float válidos
                        lon = float(status.ultimo_lon)
                        lat = float(status.ultimo_lat)
                        p = Point(lon, lat, srid=4326)
                        # Buscar zona que contenga el punto
                        zona = Zona.objects.filter(geom__contains=p, visible=True).first()
                        if zona:
                            zona_nombre = zona.nombre
                    except (ImportError, OSError):
                        # Django GIS no disponible (GDAL no instalado), saltar verificación de zona
                        pass
                    except Exception as e:
                        # Silenciar error de zona para no romper todo el reporte
                        print(f"Error verificando zona para {nombre}: {e}")
                        pass
                
                if zona_nombre:
                    ubicacion_str = f"Zona {zona_nombre}"
                elif hasattr(movil, 'geocode') and movil.geocode:
                    geo = movil.geocode
                    # Priorizar calle y altura si existen para evitar mostrar solo números
                    if geo.calle:
                        ubicacion_str = f"{geo.calle} {geo.numero or ''}".strip()
                    elif geo.direccion_formateada:
                        ubicacion_str = geo.direccion_formateada.split(',')[0]
                    else:
                        ubicacion_str = geo.localidad or "Sin dirección"
                
                texto += f"{icono} *{nombre}*: {estado_str} en {ubicacion_str}\n"
                
                # Preparar frase para audio (solo para pocos móviles o resumen)
                if len(moviles_status) <= 5:
                    detalles_audio.append(f"{nombre} {estado_str} en {ubicacion_str}")

            # Resumen final
            texto += f"\nTotal: {circulando} circulando, {detenidos} detenidos."
            
            audio = f"Reporte de flota: {circulando} circulando y {detenidos} detenidos."
            if detalles_audio:
                audio += " " + ". ".join(detalles_audio) + "."
            
            return {
                'texto': texto,
                'audio': audio
            }

        except Exception as e:
            print(f"Error en situación de flota: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Error al generar reporte de flota.",
                'audio': "No pude generar el reporte de situación de flota."
            }

    def _moviles_en_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Lista móviles dentro de una zona específica.
        """
        try:
            # 1. Identificar la zona
            texto_completo = variables.get('_texto_completo', '')
            nombre_zona = variables.get('zona', '')
            
            # Si no vino la variable 'zona' limpia, intentar extraerla del texto
            if not nombre_zona:
                # Intentar extraer con regex primero (más preciso)
                import re
                patrones = [
                    r'(?:moviles?|móviles?|vehiculos?|autos?)\s+(?:en|dentro\s+de|de\s+la)\s+(?:zona\s+)?(.+)',
                    r'zona\s+(.+)',
                    r'(?:en|dentro\s+de)\s+(?:la\s+)?zona\s+(.+)',
                ]
                
                texto_lower = texto_completo.lower()
                for patron in patrones:
                    match = re.search(patron, texto_lower, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        # Limpiar puntuación final
                        nombre_zona = re.sub(r'[?.,!;:]+$', '', nombre_zona).strip()
                        if nombre_zona:
                            break
                
                # Si no se extrajo con regex, usar método simple
                if not nombre_zona:
                    clean = texto_completo.lower()
                    for w in ['moviles', 'móviles', 'en', 'zona', 'la', 'dentro', 'de', 'vehiculos', 'autos', 'quien', 'esta', 'está']:
                        clean = clean.replace(w, '')
                    nombre_zona = clean.strip()
            
            if not nombre_zona:
                return {
                    'texto': "Por favor indicame el nombre de la zona.",
                    'audio': "¿De qué zona querés ver los móviles?"
                }

            # Obtener usuario si está disponible
            usuario = variables.get('_usuario')
            
            # Buscar la zona
            resultado_zona = self._buscar_zona_por_nombre(nombre_zona, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré ninguna zona llamada '{nombre_zona}'.",
                    'audio': f"No encontré la zona {nombre_zona}."
                }
            
            zona_obj, _, _, nombre_real = resultado_zona
            
            # 2. Buscar móviles dentro de la zona (PostGIS)
            # Asumimos que MovilStatus tiene lat/lon pero no necesariamente un campo Point indexado en todos los modelos legacy.
            # Pero si usamos Django GIS, podemos construir el punto al vuelo o filtrar.
            # Lo más eficiente si MovilStatus no tiene PointField es iterar (si son pocos) o usar raw SQL.
            # Vamos a intentar usar __contains con Point construido si es posible, o iterar si falla.
            
            moviles_en_zona = []
            
            # Opción A: Iterar activos y chequear (más seguro si no hay índice espacial en status)
            activos = MovilStatus.objects.filter(
                fecha_gps__gte=timezone.now() - timedelta(hours=24)
            ).select_related('movil')
            
            # Intentar usar Django GIS si está disponible
            try:
                from django.contrib.gis.geos import Point
                usar_gis = True
            except (ImportError, OSError) as e:
                usar_gis = False
                print(f"⚠️ Django GIS no disponible (error: {e}), usando verificación simple")
            
            for status in activos:
                if status.ultimo_lat and status.ultimo_lon:
                    try:
                        encontrado = False
                        if usar_gis:
                            try:
                                # Usar Point con SRID 4326 (WGS84)
                                p = Point(float(status.ultimo_lon), float(status.ultimo_lat), srid=4326)
                                if zona_obj.geom and zona_obj.geom.contains(p):
                                    moviles_en_zona.append(status)
                                    encontrado = True
                                    continue  # Si se encontró con GIS, pasar al siguiente móvil
                            except (OSError, AttributeError) as gis_error:
                                # GDAL no disponible o error al acceder a geom
                                print(f"⚠️ Error GIS al verificar posición para {status.movil} (usando fallback): {gis_error}")
                                # Continuar con fallback simple para este móvil
                                encontrado = False
                        
                        # Fallback: verificación simple por distancia (menos preciso)
                        # Solo si no se encontró con GIS o GIS no está disponible
                        if not encontrado:
                            # Solo si la zona tiene un centro aproximado
                            if hasattr(zona_obj, 'centro_lat') and hasattr(zona_obj, 'centro_lon'):
                                # Calcular distancia simple (Haversine aproximado)
                                lat_zona = float(zona_obj.centro_lat)
                                lon_zona = float(zona_obj.centro_lon)
                                lat_movil = float(status.ultimo_lat)
                                lon_movil = float(status.ultimo_lon)
                                
                                # Distancia aproximada en grados (muy simplificado)
                                dist_lat = abs(lat_movil - lat_zona)
                                dist_lon = abs(lon_movil - lon_zona)
                                # Aproximación: 1 grado ≈ 111 km
                                # Si la zona tiene un radio, usar ese, sino usar 0.01 grados (~1km)
                                radio_grados = getattr(zona_obj, 'radio_metros', 1000) / 111000.0
                                
                                if dist_lat < radio_grados and dist_lon < radio_grados:
                                    moviles_en_zona.append(status)
                    except Exception as e:
                        print(f"Error verificando posición para {status.movil}: {e}")
                        continue
            
            cantidad = len(moviles_en_zona)
            
            if cantidad == 0:
                return {
                    'texto': f"No hay móviles activos dentro de *{nombre_real}*.",
                    'audio': f"No hay móviles en la zona {nombre_real}."
                }
            
            texto = f"📍 *Móviles en {nombre_real}* ({cantidad})\n\n"
            nombres = []
            
            for status in moviles_en_zona:
                movil = status.movil
                nombre = movil.alias or movil.patente
                
                # Calcular tiempo de permanencia (complejo, simplificamos a hora reporte)
                hora = status.fecha_gps.strftime('%H:%M')
                texto += f"• *{nombre}* (Reporte: {hora})\n"
                nombres.append(nombre)
            
            audio = f"Hay {cantidad} móviles en {nombre_real}. "
            if cantidad <= 5:
                audio += "Son: " + ", ".join(nombres) + "."
            
            return {
                'texto': texto,
                'audio': audio
            }

        except Exception as e:
            print(f"Error buscando móviles en zona: {e}")
            return {
                'texto': "Ocurrió un error al buscar en la zona.",
                'audio': "Tuve un problema buscando en esa zona."
            }
    
    def _moviles_fuera_de_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Lista móviles que están fuera de una zona específica.
        """
        try:
            # 1. Identificar la zona
            texto_completo = variables.get('_texto_completo', '')
            nombre_zona = variables.get('zona', '')
            
            # Si no vino la variable 'zona' limpia, intentar extraerla del texto
            if not nombre_zona:
                # Intentar extraer con regex primero (más preciso)
                import re
                patrones = [
                    # Patrones con "zona" explícita
                    r'(?:moviles?|móviles?|vehiculos?|autos?)\s+(?:fuera\s+de|afuera\s+de|no\s+est[aá]n?\s+en)\s+(?:la\s+)?zona\s+(.+)',
                    r'fuera\s+de\s+(?:la\s+)?zona\s+(.+)',
                    r'afuera\s+de\s+(?:la\s+)?zona\s+(.+)',
                    r'(?:moviles?|móviles?|vehiculos?|autos?)\s+que\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona\s+(.+)',
                    # Patrones sin "zona" explícita (solo el nombre de la zona)
                    r'(?:moviles?|móviles?|vehiculos?|autos?)\s+(?:fuera\s+de|afuera\s+de)\s+(.+)',
                    r'que\s+(?:moviles?|móviles?|vehiculos?|autos?)\s+est[aá]n?\s+(?:fuera\s+de|afuera\s+de)\s+(.+)',
                    r'que\s+(?:moviles?|móviles?|vehiculos?|autos?)\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona\s+(.+)',
                    r'que\s+(?:moviles?|móviles?|vehiculos?|autos?)\s+no\s+est[aá]n?\s+en\s+(.+)',
                    r'cuales?\s+salieron\s+de\s+(.+)',
                    r'quienes?\s+salieron\s+de\s+(.+)',
                    r'quien\s+salio\s+de\s+(.+)',
                    r'quien\s+sali[oó]\s+de\s+(.+)',
                ]
                
                texto_lower = texto_completo.lower()
                for patron in patrones:
                    match = re.search(patron, texto_lower, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        # Limpiar puntuación final
                        nombre_zona = re.sub(r'[?.,!;:]+$', '', nombre_zona).strip()
                        # Remover "zona" si quedó al inicio
                        nombre_zona = re.sub(r'^zona\s+', '', nombre_zona, flags=re.IGNORECASE).strip()
                        if nombre_zona:
                            break
                
                # Si no se extrajo con regex, usar método simple
                if not nombre_zona:
                    clean = texto_completo.lower()
                    # Remover palabras comunes
                    palabras_remover = ['moviles', 'móviles', 'fuera', 'de', 'zona', 'la', 'vehiculos', 'vehículos', 'autos', 'que', 'no', 'estan', 'están', 'en', 'afuera', 'salieron', 'salio', 'salió', 'cuales', 'quienes', 'quien']
                    for w in palabras_remover:
                        clean = re.sub(r'\b' + re.escape(w) + r'\b', '', clean, flags=re.IGNORECASE)
                    nombre_zona = clean.strip()
            
            if not nombre_zona:
                return {
                    'texto': "Por favor indicame el nombre de la zona.",
                    'audio': "¿De qué zona querés ver los móviles que están fuera?"
                }

            # Obtener usuario si está disponible
            usuario = variables.get('_usuario')
            
            # Buscar la zona
            resultado_zona = self._buscar_zona_por_nombre(nombre_zona, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré ninguna zona llamada '{nombre_zona}'.",
                    'audio': f"No encontré la zona {nombre_zona}."
                }
            
            zona_obj, _, _, nombre_real = resultado_zona
            
            # 2. Buscar móviles FUERA de la zona (inverso de _moviles_en_zona)
            # Obtener todos los móviles activos
            activos = MovilStatus.objects.filter(
                fecha_gps__gte=timezone.now() - timedelta(hours=24)
            ).select_related('movil')
            
            # Intentar usar Django GIS si está disponible
            try:
                from django.contrib.gis.geos import Point
                usar_gis = True
            except (ImportError, OSError) as e:
                usar_gis = False
                print(f"⚠️ Django GIS no disponible (error: {e}), usando verificación simple")
            
            moviles_fuera_de_zona = []
            
            for status in activos:
                if status.ultimo_lat and status.ultimo_lon:
                    try:
                        esta_dentro = False
                        if usar_gis:
                            try:
                                # Usar Point con SRID 4326 (WGS84)
                                p = Point(float(status.ultimo_lon), float(status.ultimo_lat), srid=4326)
                                if zona_obj.geom and zona_obj.geom.contains(p):
                                    esta_dentro = True
                                    continue  # Si está dentro, no agregarlo a la lista
                            except (OSError, AttributeError) as gis_error:
                                # GDAL no disponible o error al acceder a geom
                                print(f"⚠️ Error GIS al verificar posición para {status.movil} (usando fallback): {gis_error}")
                                esta_dentro = False
                        
                        # Fallback: verificación simple por distancia (menos preciso)
                        # Solo si no se verificó con GIS o GIS no está disponible
                        if not esta_dentro and not usar_gis:
                            # Solo si la zona tiene un centro aproximado
                            if hasattr(zona_obj, 'centro_lat') and hasattr(zona_obj, 'centro_lon'):
                                # Calcular distancia simple (Haversine aproximado)
                                lat_zona = float(zona_obj.centro_lat)
                                lon_zona = float(zona_obj.centro_lon)
                                lat_movil = float(status.ultimo_lat)
                                lon_movil = float(status.ultimo_lon)
                                
                                # Distancia aproximada en grados (muy simplificado)
                                dist_lat = abs(lat_movil - lat_zona)
                                dist_lon = abs(lon_movil - lon_zona)
                                # Aproximación: 1 grado ≈ 111 km
                                # Si la zona tiene un radio, usar ese, sino usar 0.01 grados (~1km)
                                radio_grados = getattr(zona_obj, 'radio_metros', 1000) / 111000.0
                                
                                if dist_lat < radio_grados and dist_lon < radio_grados:
                                    esta_dentro = True
                        
                        # Si NO está dentro, agregarlo a la lista de fuera
                        if not esta_dentro:
                            moviles_fuera_de_zona.append(status)
                    except Exception as e:
                        print(f"Error verificando posición para {status.movil}: {e}")
                        # En caso de error, considerar que está fuera (más seguro)
                        moviles_fuera_de_zona.append(status)
                        continue
            
            cantidad = len(moviles_fuera_de_zona)
            
            if cantidad == 0:
                return {
                    'texto': f"Todos los móviles activos están dentro de *{nombre_real}*.",
                    'audio': f"Todos los móviles están dentro de la zona {nombre_real}."
                }
            
            texto = f"🚫 *Móviles fuera de {nombre_real}* ({cantidad})\n\n"
            nombres = []
            
            for status in moviles_fuera_de_zona:
                movil = status.movil
                nombre = movil.alias or movil.patente
                
                # Calcular tiempo de permanencia (complejo, simplificamos a hora reporte)
                hora = status.fecha_gps.strftime('%H:%M')
                texto += f"• *{nombre}* (Reporte: {hora})\n"
                nombres.append(nombre)
            
            audio = f"Hay {cantidad} móviles fuera de {nombre_real}. "
            if cantidad <= 5:
                audio += "Son: " + ", ".join(nombres) + "."
            
            return {
                'texto': texto,
                'audio': audio
            }

        except Exception as e:
            print(f"Error buscando móviles fuera de zona: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al buscar móviles fuera de la zona.",
                'audio': "Tuve un problema buscando móviles fuera de esa zona."
            }

    def _ingreso_a_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Busca en el histórico (últimos 2 días) cuándo un móvil ingresó a una zona.
        """
        try:
            from gps.models import Posicion
            from django.contrib.gis.geos import Point
            
            texto_completo = variables.get('_texto_completo', '')
            
            # Extraer móvil
            movil_nombre = variables.get('movil', '').strip()
            if not movil_nombre:
                # Intentar extraer del texto
                movil_nombre = self.matcher.extraer_movil(texto_completo) if hasattr(self, 'matcher') else None
                if not movil_nombre:
                    # Usar método manual
                    texto_normalizado = ''.join(
                        c for c in unicodedata.normalize('NFD', texto_completo)
                        if unicodedata.category(c) != 'Mn'
                    )
                    patron_patente = r'\b([A-Z]{2,5})\s*(\d{2,4})\b'
                    match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                    if match:
                        movil_nombre = (match.group(1) + match.group(2)).upper()
            
            # Si aún no hay móvil, usar el del contexto (último móvil consultado)
            if not movil_nombre:
                movil_nombre = variables.get('_ultimo_movil', '').strip()
                if movil_nombre:
                    print(f"📍 [CONTEXTO] Usando móvil del contexto: '{movil_nombre}'")
            
            if not movil_nombre:
                return {
                    'texto': "Por favor indicame qué móvil necesitas consultar.",
                    'audio': "¿Qué móvil querés consultar?"
                }
            
            # Buscar móvil
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).first()
            
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'.",
                    'audio': f"No encontré el móvil {movil_nombre}."
                }
            
            # Extraer zona
            nombre_zona = variables.get('zona', '').strip()
            if not nombre_zona:
                # Intentar extraer del texto
                patrones = [
                    r'(?:a\s+que\s+hora|en\s+que\s+momento|cu[aá]ndo)\s+(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'ingreso\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'ingres[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'entr[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'entro\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'zona\s+(\w+(?:\s+\w+)?)',
                ]
                texto_lower = texto_completo.lower()
                for patron in patrones:
                    match = re.search(patron, texto_lower, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        nombre_zona = re.sub(r'[?.,!;:]+$', '', nombre_zona).strip()
                        # Remover "el movil X" si quedó en el nombre
                        nombre_zona = re.sub(r'^\s*(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+', '', nombre_zona, flags=re.IGNORECASE).strip()
                        if nombre_zona:
                            break
            
            # Si aún no hay zona, usar la del contexto (última zona consultada)
            if not nombre_zona:
                nombre_zona = variables.get('_ultimo_destino', '').strip()
                if nombre_zona:
                    print(f"📍 [CONTEXTO] Usando zona del contexto: '{nombre_zona}'")
            
            if not nombre_zona:
                return {
                    'texto': "Por favor indicame el nombre de la zona.",
                    'audio': "¿A qué zona querés consultar el ingreso?"
                }
            
            # Buscar zona
            usuario = variables.get('_usuario')
            resultado_zona = self._buscar_zona_por_nombre(nombre_zona, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré la zona '{nombre_zona}'.",
                    'audio': f"No encontré la zona {nombre_zona}."
                }
            
            zona_obj, _, _, nombre_real = resultado_zona
            
            # Buscar posiciones del móvil en los últimos 2 días, ordenadas por fecha
            fecha_limite = timezone.now() - timedelta(days=2)
            posiciones = Posicion.objects.filter(
                movil=movil,
                fec_gps__gte=fecha_limite,
                lat__isnull=False,
                lon__isnull=False,
                is_valid=True
            ).order_by('fec_gps')
            
            # Buscar la primera posición dentro de la zona
            primera_ingreso = None
            posicion_anterior_fuera = True  # Asumimos que antes estaba fuera
            
            for pos in posiciones:
                if pos.lat and pos.lon:
                    try:
                        p = Point(float(pos.lon), float(pos.lat), srid=4326)
                        if zona_obj.geom and zona_obj.geom.contains(p):
                            # Si la posición anterior estaba fuera y esta está dentro, es el ingreso
                            if posicion_anterior_fuera:
                                primera_ingreso = pos
                                break
                        else:
                            # Está fuera, marcar para la próxima iteración
                            posicion_anterior_fuera = True
                    except Exception as e:
                        print(f"Error verificando posición {pos.id}: {e}")
                        continue
            
            if not primera_ingreso:
                return {
                    'texto': f"*{movil.alias or movil.patente}* no ingresó a *{nombre_real}* en los últimos 2 días.",
                    'audio': f"{movil.alias or movil.patente} no ingresó a {nombre_real} en los últimos 2 días."
                }
            
            # Formatear respuesta
            fecha_ingreso = primera_ingreso.fec_gps
            fecha_str = fecha_ingreso.strftime('%d/%m/%Y %H:%M')
            
            texto = f"✅ *{movil.alias or movil.patente}* ingresó a *{nombre_real}* el {fecha_str}."
            audio = f"{movil.alias or movil.patente} ingresó a {nombre_real} el {fecha_str}."
            
            return {
                'texto': texto,
                'audio': audio
            }
            
        except Exception as e:
            print(f"Error buscando ingreso a zona: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al buscar el ingreso a la zona.",
                'audio': "Tuve un problema buscando el ingreso."
            }

    def _salio_de_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Busca en el histórico (últimos 2 días) cuándo un móvil salió de una zona.
        """
        try:
            from gps.models import Posicion
            from django.contrib.gis.geos import Point
            
            texto_completo = variables.get('_texto_completo', '')
            
            # Extraer móvil
            movil_nombre = variables.get('movil', '').strip()
            if not movil_nombre:
                texto_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', texto_completo)
                    if unicodedata.category(c) != 'Mn'
                )
                patron_patente = r'\b([A-Z]{2,5})\s*(\d{2,4})\b'
                match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_nombre = (match.group(1) + match.group(2)).upper()
            
            # Si aún no hay móvil, usar el del contexto (último móvil consultado)
            if not movil_nombre:
                movil_nombre = variables.get('_ultimo_movil', '').strip()
                if movil_nombre:
                    print(f"📍 [CONTEXTO] Usando móvil del contexto: '{movil_nombre}'")
            
            if not movil_nombre:
                return {
                    'texto': "Por favor indicame qué móvil necesitas consultar.",
                    'audio': "¿Qué móvil querés consultar?"
                }
            
            # Buscar móvil
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).first()
            
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'.",
                    'audio': f"No encontré el móvil {movil_nombre}."
                }
            
            # Extraer zona
            nombre_zona = variables.get('zona', '').strip()
            if not nombre_zona:
                patrones = [
                    r'(?:a\s+que\s+hora|en\s+que\s+momento|cu[aá]ndo)\s+(?:sali[oó]|salido|salida)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'sali[oó]\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'sali[oó]\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'salido\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'salida\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'zona\s+(\w+(?:\s+\w+)?)',
                ]
                texto_lower = texto_completo.lower()
                for patron in patrones:
                    match = re.search(patron, texto_lower, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        nombre_zona = re.sub(r'[?.,!;:]+$', '', nombre_zona).strip()
                        # Remover "el movil X" si quedó en el nombre
                        nombre_zona = re.sub(r'^\s*(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+', '', nombre_zona, flags=re.IGNORECASE).strip()
                        if nombre_zona:
                            break
            
            # Si aún no hay zona, usar la del contexto (última zona consultada)
            if not nombre_zona:
                nombre_zona = variables.get('_ultimo_destino', '').strip()
                if nombre_zona:
                    print(f"📍 [CONTEXTO] Usando zona del contexto: '{nombre_zona}'")
            
            if not nombre_zona:
                return {
                    'texto': "Por favor indicame el nombre de la zona.",
                    'audio': "¿De qué zona querés consultar la salida?"
                }
            
            # Buscar zona
            usuario = variables.get('_usuario')
            resultado_zona = self._buscar_zona_por_nombre(nombre_zona, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré la zona '{nombre_zona}'.",
                    'audio': f"No encontré la zona {nombre_zona}."
                }
            
            zona_obj, _, _, nombre_real = resultado_zona
            
            # Buscar posiciones del móvil en los últimos 2 días, ordenadas por fecha
            fecha_limite = timezone.now() - timedelta(days=2)
            posiciones = Posicion.objects.filter(
                movil=movil,
                fec_gps__gte=fecha_limite,
                lat__isnull=False,
                lon__isnull=False,
                is_valid=True
            ).order_by('fec_gps')
            
            # Buscar la última posición dentro seguida de una fuera
            ultima_salida = None
            posicion_anterior_dentro = False
            
            for pos in posiciones:
                if pos.lat and pos.lon:
                    try:
                        p = Point(float(pos.lon), float(pos.lat), srid=4326)
                        if zona_obj.geom and zona_obj.geom.contains(p):
                            # Está dentro
                            posicion_anterior_dentro = True
                        else:
                            # Está fuera
                            # Si la posición anterior estaba dentro, esta es la salida
                            if posicion_anterior_dentro:
                                ultima_salida = pos
                                # Continuar buscando por si hay múltiples salidas
                            posicion_anterior_dentro = False
                    except Exception as e:
                        print(f"Error verificando posición {pos.id}: {e}")
                        continue
            
            if not ultima_salida:
                return {
                    'texto': f"*{movil.alias or movil.patente}* no salió de *{nombre_real}* en los últimos 2 días.",
                    'audio': f"{movil.alias or movil.patente} no salió de {nombre_real} en los últimos 2 días."
                }
            
            # Formatear respuesta
            fecha_salida = ultima_salida.fec_gps
            fecha_str = fecha_salida.strftime('%d/%m/%Y %H:%M')
            
            texto = f"🚪 *{movil.alias or movil.patente}* salió de *{nombre_real}* el {fecha_str}."
            audio = f"{movil.alias or movil.patente} salió de {nombre_real} el {fecha_str}."
            
            return {
                'texto': texto,
                'audio': audio
            }
            
        except Exception as e:
            print(f"Error buscando salida de zona: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al buscar la salida de la zona.",
                'audio': "Tuve un problema buscando la salida."
            }

    def _paso_por_zona(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Busca en el histórico (últimos 2 días) cuándo un móvil pasó por una zona.
        """
        try:
            from gps.models import Posicion
            from django.contrib.gis.geos import Point
            
            texto_completo = variables.get('_texto_completo', '')
            
            # Extraer móvil
            movil_nombre = variables.get('movil', '').strip()
            if not movil_nombre:
                texto_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', texto_completo)
                    if unicodedata.category(c) != 'Mn'
                )
                patron_patente = r'\b([A-Z]{2,5})\s*(\d{2,4})\b'
                match = re.search(patron_patente, texto_normalizado, re.IGNORECASE)
                if match:
                    movil_nombre = (match.group(1) + match.group(2)).upper()
            
            # Si aún no hay móvil, usar el del contexto (último móvil consultado)
            if not movil_nombre:
                movil_nombre = variables.get('_ultimo_movil', '').strip()
                if movil_nombre:
                    print(f"📍 [CONTEXTO] Usando móvil del contexto: '{movil_nombre}'")
            
            if not movil_nombre:
                return {
                    'texto': "Por favor indicame qué móvil necesitas consultar.",
                    'audio': "¿Qué móvil querés consultar?"
                }
            
            # Buscar móvil
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).first()
            
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'.",
                    'audio': f"No encontré el móvil {movil_nombre}."
                }
            
            # Extraer zona
            nombre_zona = variables.get('zona', '').strip()
            if not nombre_zona:
                patrones = [
                    r'(?:a\s+que\s+hora|en\s+que\s+momento|cu[aá]ndo)\s+(?:pas[oó]|paso|estuvo)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+(?:por|por\s+la|en|en\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'paso\s+(?:por|por\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'estuvo\s+(?:en|en\s+la)\s+(?:la\s+)?zona\s+(\w+(?:\s+\w+)?)',
                    r'zona\s+(\w+(?:\s+\w+)?)',
                ]
                texto_lower = texto_completo.lower()
                for patron in patrones:
                    match = re.search(patron, texto_lower, re.IGNORECASE)
                    if match:
                        nombre_zona = match.group(1).strip()
                        nombre_zona = re.sub(r'[?.,!;:]+$', '', nombre_zona).strip()
                        # Remover "el movil X" si quedó en el nombre
                        nombre_zona = re.sub(r'^\s*(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+', '', nombre_zona, flags=re.IGNORECASE).strip()
                        if nombre_zona:
                            break
            
            # Si aún no hay zona, usar la del contexto (última zona consultada)
            if not nombre_zona:
                nombre_zona = variables.get('_ultimo_destino', '').strip()
                if nombre_zona:
                    print(f"📍 [CONTEXTO] Usando zona del contexto: '{nombre_zona}'")
            
            if not nombre_zona:
                return {
                    'texto': "Por favor indicame el nombre de la zona.",
                    'audio': "¿Por qué zona querés consultar?"
                }
            
            # Buscar zona
            usuario = variables.get('_usuario')
            resultado_zona = self._buscar_zona_por_nombre(nombre_zona, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré la zona '{nombre_zona}'.",
                    'audio': f"No encontré la zona {nombre_zona}."
                }
            
            zona_obj, _, _, nombre_real = resultado_zona
            
            # Buscar posiciones del móvil en los últimos 2 días, ordenadas por fecha
            fecha_limite = timezone.now() - timedelta(days=2)
            posiciones = Posicion.objects.filter(
                movil=movil,
                fec_gps__gte=fecha_limite,
                lat__isnull=False,
                lon__isnull=False,
                is_valid=True
            ).order_by('fec_gps')
            
            # Buscar todas las posiciones dentro de la zona
            posiciones_en_zona = []
            
            for pos in posiciones:
                if pos.lat and pos.lon:
                    try:
                        p = Point(float(pos.lon), float(pos.lat), srid=4326)
                        if zona_obj.geom and zona_obj.geom.contains(p):
                            posiciones_en_zona.append(pos)
                    except Exception as e:
                        print(f"Error verificando posición {pos.id}: {e}")
                        continue
            
            if not posiciones_en_zona:
                return {
                    'texto': f"*{movil.alias or movil.patente}* no pasó por *{nombre_real}* en los últimos 2 días.",
                    'audio': f"{movil.alias or movil.patente} no pasó por {nombre_real} en los últimos 2 días."
                }
            
            # Formatear respuesta
            cantidad = len(posiciones_en_zona)
            primera = posiciones_en_zona[0]
            ultima = posiciones_en_zona[-1]
            
            fecha_primera = primera.fec_gps.strftime('%d/%m/%Y %H:%M')
            fecha_ultima = ultima.fec_gps.strftime('%d/%m/%Y %H:%M')
            
            if cantidad == 1:
                texto = f"📍 *{movil.alias or movil.patente}* pasó por *{nombre_real}* el {fecha_primera}."
                audio = f"{movil.alias or movil.patente} pasó por {nombre_real} el {fecha_primera}."
            else:
                texto = f"📍 *{movil.alias or movil.patente}* pasó por *{nombre_real}* {cantidad} veces en los últimos 2 días.\n"
                texto += f"• Primera vez: {fecha_primera}\n"
                texto += f"• Última vez: {fecha_ultima}"
                audio = f"{movil.alias or movil.patente} pasó por {nombre_real} {cantidad} veces. Primera vez el {fecha_primera}, última vez el {fecha_ultima}."
            
            return {
                'texto': texto,
                'audio': audio
            }
            
        except Exception as e:
            print(f"Error buscando paso por zona: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al buscar el paso por la zona.",
                'audio': "Tuve un problema buscando el paso por la zona."
            }

    def _calcular_distancia_moviles(self, movil1_nombre: str, movil2_nombre: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Calcula la distancia entre dos móviles.
        """
        try:
            # Buscar ambos móviles
            movil1 = Movil.objects.filter(
                Q(patente__icontains=movil1_nombre) |
                Q(alias__icontains=movil1_nombre) |
                Q(codigo__icontains=movil1_nombre)
            ).first()
            
            movil2 = Movil.objects.filter(
                Q(patente__icontains=movil2_nombre) |
                Q(alias__icontains=movil2_nombre) |
                Q(codigo__icontains=movil2_nombre)
            ).first()
            
            if not movil1:
                return {
                    'texto': f"No encontré el móvil '{movil1_nombre}'.",
                    'audio': f"No encontré el móvil {movil1_nombre}."
                }
            
            if not movil2:
                return {
                    'texto': f"No encontré el móvil '{movil2_nombre}'.",
                    'audio': f"No encontré el móvil {movil2_nombre}."
                }
            
            # Obtener posiciones actuales
            status1 = MovilStatus.objects.filter(movil=movil1).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh').first()
            status2 = MovilStatus.objects.filter(movil=movil2).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh').first()
            
            if not status1 or not status1.ultimo_lat or not status1.ultimo_lon:
                return {
                    'texto': f"El móvil '{movil1.alias or movil1.patente}' no tiene posición actual.",
                    'audio': f"{movil1.alias or movil1.patente} no tiene posición actual."
                }
            
            if not status2 or not status2.ultimo_lat or not status2.ultimo_lon:
                return {
                    'texto': f"El móvil '{movil2.alias or movil2.patente}' no tiene posición actual.",
                    'audio': f"{movil2.alias or movil2.patente} no tiene posición actual."
                }
            
            lat1 = float(status1.ultimo_lat)
            lon1 = float(status1.ultimo_lon)
            lat2 = float(status2.ultimo_lat)
            lon2 = float(status2.ultimo_lon)
            
            # Calcular distancia usando OSRM
            cache_key_osrm = f'osrm_{lat1}_{lon1}_{lat2}_{lon2}'
            osrm = cache.get(cache_key_osrm)
            if osrm is None:
                try:
                    osrm_url = (
                        f"http://router.project-osrm.org/route/v1/driving/"
                        f"{lon1},{lat1};{lon2},{lat2}?overview=false&alternatives=false"
                    )
                    osrm_resp = requests.get(osrm_url, timeout=3)
                    osrm_resp.raise_for_status()
                    osrm = osrm_resp.json()
                    cache.set(cache_key_osrm, osrm, 3600)
                except Exception:
                    osrm = {}
            
            try:
                routes = osrm.get("routes") or []
                if routes:
                    duration_sec = float(routes[0]["duration"])
                    distance_m = float(routes[0]["distance"])
                else:
                    raise ValueError("Sin rutas")
            except Exception:
                # Fallback: distancia geodésica
                def haversine(lon1, lat1, lon2, lat2):
                    R = 6371.0
                    dLat = radians(lat2 - lat1)
                    dLon = radians(lon2 - lon1)
                    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                dist_km = haversine(lon1, lat1, lon2, lat2)
                est_vel_kmh = float(status1.ultima_velocidad_kmh or 50.0) or 50.0
                duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                distance_m = dist_km * 1000.0
            
            distancia_km = distance_m / 1000.0
            duracion_min = duration_sec / 60.0
            
            nombre1 = movil1.alias or movil1.patente
            nombre2 = movil2.alias or movil2.patente
            
            texto = (
                f"📍 Distancia entre *{nombre1}* y *{nombre2}*:\n"
                f"• Distancia: {distancia_km:.1f} km\n"
                f"• Tiempo estimado: {int(duracion_min)} min"
            )
            audio = (
                f"La distancia entre {nombre1} y {nombre2} es de {distancia_km:.1f} kilómetros, "
                f"con un tiempo estimado de {int(duracion_min)} minutos."
            )
            return {
                'texto': texto,
                'audio': audio
            }
        except Exception as e:
            print(f"Error calculando distancia entre móviles: {e}")
            return {
                'texto': "Error al calcular la distancia entre los móviles.",
                'audio': "No pude calcular la distancia."
            }
    
    def _calcular_distancia_movil_zona(self, movil_nombre: str, zona_nombre: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Calcula la distancia entre un móvil y una zona.
        """
        try:
            # Buscar móvil
            movil = Movil.objects.filter(
                Q(patente__icontains=movil_nombre) |
                Q(alias__icontains=movil_nombre) |
                Q(codigo__icontains=movil_nombre)
            ).first()
            
            if not movil:
                return {
                    'texto': f"No encontré el móvil '{movil_nombre}'.",
                    'audio': f"No encontré el móvil {movil_nombre}."
                }
            
            # Obtener posición del móvil
            status = MovilStatus.objects.filter(movil=movil).only('ultimo_lat', 'ultimo_lon', 'ultima_velocidad_kmh').first()
            if not status or not status.ultimo_lat or not status.ultimo_lon:
                return {
                    'texto': f"El móvil '{movil.alias or movil.patente}' no tiene posición actual.",
                    'audio': f"{movil.alias or movil.patente} no tiene posición actual."
                }
            
            lat_movil = float(status.ultimo_lat)
            lon_movil = float(status.ultimo_lon)
            
            # Buscar zona
            usuario = variables.get('_usuario')
            resultado_zona = self._buscar_zona_por_nombre(zona_nombre, usuario)
            if not resultado_zona:
                return {
                    'texto': f"No encontré la zona '{zona_nombre}'.",
                    'audio': f"No encontré la zona {zona_nombre}."
                }
            
            zona_obj, lat_zona, lon_zona, nombre_zona = resultado_zona
            
            # Calcular distancia usando OSRM
            cache_key_osrm = f'osrm_{lat_movil}_{lon_movil}_{lat_zona}_{lon_zona}'
            osrm = cache.get(cache_key_osrm)
            if osrm is None:
                try:
                    osrm_url = (
                        f"http://router.project-osrm.org/route/v1/driving/"
                        f"{lon_movil},{lat_movil};{lon_zona},{lat_zona}?overview=false&alternatives=false"
                    )
                    osrm_resp = requests.get(osrm_url, timeout=3)
                    osrm_resp.raise_for_status()
                    osrm = osrm_resp.json()
                    cache.set(cache_key_osrm, osrm, 3600)
                except Exception:
                    osrm = {}
            
            try:
                routes = osrm.get("routes") or []
                if routes:
                    duration_sec = float(routes[0]["duration"])
                    distance_m = float(routes[0]["distance"])
                else:
                    raise ValueError("Sin rutas")
            except Exception:
                # Fallback: distancia geodésica
                def haversine(lon1, lat1, lon2, lat2):
                    R = 6371.0
                    dLat = radians(lat2 - lat1)
                    dLon = radians(lon2 - lon1)
                    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                dist_km = haversine(lon_movil, lat_movil, lon_zona, lat_zona)
                est_vel_kmh = float(status.ultima_velocidad_kmh or 50.0) or 50.0
                duration_sec = (dist_km / max(est_vel_kmh, 5.0)) * 3600.0
                distance_m = dist_km * 1000.0
            
            distancia_km = distance_m / 1000.0
            duracion_min = duration_sec / 60.0
            
            nombre_movil = movil.alias or movil.patente
            
            texto = (
                f"📍 Distancia entre *{nombre_movil}* y *{nombre_zona}*:\n"
                f"• Distancia: {distancia_km:.1f} km\n"
                f"• Tiempo estimado: {int(duracion_min)} min"
            )
            audio = (
                f"La distancia entre {nombre_movil} y {nombre_zona} es de {distancia_km:.1f} kilómetros, "
                f"con un tiempo estimado de {int(duracion_min)} minutos."
            )
            return {
                'texto': texto,
                'audio': audio
            }
        except Exception as e:
            print(f"Error calculando distancia entre móvil y zona: {e}")
            return {
                'texto': "Error al calcular la distancia.",
                'audio': "No pude calcular la distancia."
            }
    
    def _calcular_distancia_zonas(self, zona1_nombre: str, zona2_nombre: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Calcula la distancia entre dos zonas.
        """
        try:
            usuario = variables.get('_usuario')
            
            # Buscar ambas zonas
            resultado_zona1 = self._buscar_zona_por_nombre(zona1_nombre, usuario)
            resultado_zona2 = self._buscar_zona_por_nombre(zona2_nombre, usuario)
            
            if not resultado_zona1:
                return {
                    'texto': f"No encontré la zona '{zona1_nombre}'.",
                    'audio': f"No encontré la zona {zona1_nombre}."
                }
            
            if not resultado_zona2:
                return {
                    'texto': f"No encontré la zona '{zona2_nombre}'.",
                    'audio': f"No encontré la zona {zona2_nombre}."
                }
            
            zona1_obj, lat1, lon1, nombre1 = resultado_zona1
            zona2_obj, lat2, lon2, nombre2 = resultado_zona2
            
            # Calcular distancia usando OSRM
            cache_key_osrm = f'osrm_{lat1}_{lon1}_{lat2}_{lon2}'
            osrm = cache.get(cache_key_osrm)
            if osrm is None:
                try:
                    osrm_url = (
                        f"http://router.project-osrm.org/route/v1/driving/"
                        f"{lon1},{lat1};{lon2},{lat2}?overview=false&alternatives=false"
                    )
                    osrm_resp = requests.get(osrm_url, timeout=3)
                    osrm_resp.raise_for_status()
                    osrm = osrm_resp.json()
                    cache.set(cache_key_osrm, osrm, 3600)
                except Exception:
                    osrm = {}
            
            try:
                routes = osrm.get("routes") or []
                if routes:
                    duration_sec = float(routes[0]["duration"])
                    distance_m = float(routes[0]["distance"])
                else:
                    raise ValueError("Sin rutas")
            except Exception:
                # Fallback: distancia geodésica
                def haversine(lon1, lat1, lon2, lat2):
                    R = 6371.0
                    dLat = radians(lat2 - lat1)
                    dLon = radians(lon2 - lon1)
                    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
                    c = 2 * asin(sqrt(a))
                    return R * c
                dist_km = haversine(lon1, lat1, lon2, lat2)
                duration_sec = (dist_km / 50.0) * 3600.0  # Velocidad promedio 50 km/h
                distance_m = dist_km * 1000.0
            
            distancia_km = distance_m / 1000.0
            duracion_min = duration_sec / 60.0
            
            texto = (
                f"📍 Distancia entre *{nombre1}* y *{nombre2}*:\n"
                f"• Distancia: {distancia_km:.1f} km\n"
                f"• Tiempo estimado: {int(duracion_min)} min"
            )
            audio = (
                f"La distancia entre {nombre1} y {nombre2} es de {distancia_km:.1f} kilómetros, "
                f"con un tiempo estimado de {int(duracion_min)} minutos."
            )
            return {
                'texto': texto,
                'audio': audio
            }
        except Exception as e:
            print(f"Error calculando distancia entre zonas: {e}")
            return {
                'texto': "Error al calcular la distancia entre las zonas.",
                'audio': "No pude calcular la distancia."
            }
    
    def _ver_en_mapa(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Abre Google Maps con la posición de un móvil o el epicentro de una zona.
        """
        try:
            texto_completo = variables.get('_texto_completo', '')
            texto_lower = texto_completo.lower()
            
            # Extraer móvil o zona del texto
            movil_nombre = (variables.get('movil') or '').strip()
            zona_nombre = (variables.get('zona') or '').strip()
            
            # Si no hay móvil ni zona en variables, intentar extraer del texto
            if not movil_nombre and not zona_nombre:
                # Buscar palabras clave de zona
                patron_zona = r'\b(?:zona|deposito|almacen|base|sede|oficina|planta)\s+(\w+(?:\s+\w+)?)'
                match_zona = re.search(patron_zona, texto_lower, re.IGNORECASE)
                if match_zona:
                    zona_nombre = match_zona.group(1).strip()
                else:
                    # Intentar extraer móvil del texto
                    # Patrón para patentes tipo "ASN773", "OVV799"
                    patron_patente = r'\b([A-Z]{2,4})\s*(\d{2,4})\b'
                    match_patente = re.search(patron_patente, texto_completo, re.IGNORECASE)
                    if match_patente:
                        movil_nombre = (match_patente.group(1) + match_patente.group(2)).upper()
                    else:
                        # Buscar nombres tipo "camion3", "auto2", etc.
                        patron_nombre = r'\b(camion|auto|vehiculo|movil|móvil|unidad|truck|carro|moto)\s*(\d+)\b'
                        match_nombre = re.search(patron_nombre, texto_lower, re.IGNORECASE)
                        if match_nombre:
                            prefijo = match_nombre.group(1).upper()
                            numero = match_nombre.group(2)
                            if prefijo in ['CAMION', 'TRUCK']:
                                movil_nombre = f'CAMION{numero}'
                            elif prefijo in ['MOVIL', 'MÓVIL']:
                                movil_nombre = f'MOVIL{numero}'  # "movil" debe normalizarse a "MOVIL", no a "AUTO"
                            elif prefijo in ['AUTO', 'VEHICULO', 'CARRO', 'UNIDAD']:
                                movil_nombre = f'AUTO{numero}'
                            elif prefijo == 'MOTO':
                                movil_nombre = f'MOTO{numero}'
            
            # Si no hay móvil ni zona, usar el contexto
            if not movil_nombre and not zona_nombre:
                # PRIORIDAD 1: Intentar usar el último móvil consultado del contexto
                # Primero verificar _contexto_movil_disponible (más confiable)
                movil_contexto = (variables.get('_contexto_movil_disponible') or '').strip()
                if not movil_contexto:
                    # Fallback a movil_referencia
                    movil_contexto = (variables.get('movil_referencia') or '').strip()
                if not movil_contexto:
                    # Fallback a movil en variables
                    movil_contexto = (variables.get('movil') or '').strip()
                
                if movil_contexto:
                    movil_nombre = movil_contexto
                    print(f"🗺️ [VER_MAPA] Usando móvil del contexto: '{movil_nombre}'")
                else:
                    # Intentar usar la última zona consultada
                    zona_contexto = (variables.get('destino') or '').strip()
                    if zona_contexto:
                        # Verificar si es una zona buscándola
                        usuario = variables.get('_usuario')
                        resultado_zona = self._buscar_zona_por_nombre(zona_contexto, usuario)
                        if resultado_zona:
                            zona_nombre = zona_contexto
                            print(f"🗺️ [VER_MAPA] Usando zona del contexto: '{zona_nombre}'")
            
            # Procesar según si es móvil o zona
            if zona_nombre:
                # Buscar zona
                usuario = variables.get('_usuario')
                resultado_zona = self._buscar_zona_por_nombre(zona_nombre, usuario)
                
                if not resultado_zona:
                    return {
                        'texto': f"No encontré la zona '{zona_nombre}'.",
                        'audio': f"No encontré la zona {zona_nombre}."
                    }
                
                zona_obj, lat, lon, nombre_zona = resultado_zona
                
                # Crear link de Google Maps con el epicentro de la zona
                google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                
                texto = f"📍 Abriendo Google Maps con la ubicación de *{nombre_zona}*..."
                audio = f"Abriendo el mapa con la ubicación de {nombre_zona}."
                
                return {
                    'texto': texto,
                    'audio': audio,
                    'google_maps_link': google_maps_link
                }
            
            elif movil_nombre:
                # Buscar móvil
                movil = Movil.objects.filter(
                    Q(patente__icontains=movil_nombre) |
                    Q(alias__icontains=movil_nombre) |
                    Q(codigo__icontains=movil_nombre)
                ).first()
                
                if not movil:
                    return {
                        'texto': f"No encontré el móvil '{movil_nombre}'.",
                        'audio': f"No encontré el móvil {movil_nombre}."
                    }
                
                # Obtener posición actual
                status = MovilStatus.objects.filter(movil=movil).only('ultimo_lat', 'ultimo_lon').first()
                
                if not status or not status.ultimo_lat or not status.ultimo_lon:
                    return {
                        'texto': f"El móvil '{movil.alias or movil.patente}' no tiene posición actual.",
                        'audio': f"{movil.alias or movil.patente} no tiene posición actual."
                    }
                
                lat = float(status.ultimo_lat)
                lon = float(status.ultimo_lon)
                
                # Crear link de Google Maps
                google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                
                nombre_movil = movil.alias or movil.patente
                texto = f"📍 Abriendo Google Maps con la posición de *{nombre_movil}*..."
                audio = f"Abriendo el mapa con la posición de {nombre_movil}."
                
                return {
                    'texto': texto,
                    'audio': audio,
                    'google_maps_link': google_maps_link
                }
            else:
                return {
                    'texto': "No especificaste un móvil o zona para mostrar en el mapa.",
                    'audio': "¿Qué móvil o zona querés ver en el mapa?"
                }
        
        except Exception as e:
            print(f"Error abriendo mapa: {e}")
            import traceback
            traceback.print_exc()
            return {
                'texto': "Ocurrió un error al abrir el mapa.",
                'audio': "No pude abrir el mapa en este momento."
            }
    
    def _responder_ayuda(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Responde con ayuda sobre los comandos disponibles.
        """
        texto = "🤖 *Comandos Disponibles de SOFIA*\n\n"
        
        texto += "📋 *Flota*\n"
        texto += "• _'Listado de móviles activos'_: Ver quiénes reportaron hoy.\n"
        texto += "• _'Situación de flota'_: Resumen de quiénes circulan y quiénes están detenidos.\n\n"
        
        texto += "📍 *Zonas*\n"
        texto += "• _'Móviles en zona [Nombre]'_: Ver quiénes están en un lugar específico.\n"
        texto += "• _'Móviles fuera de zona [Nombre]'_: Ver quiénes NO están en un lugar específico.\n"
        texto += "• _'¿Dónde está el [Móvil]?'_: Ubicación actual.\n\n"
        
        texto += "🚗 *Histórico*\n"
        texto += "• _'Recorrido de [Móvil] ayer'_: Resumen de actividad.\n\n"

        texto += "⏱️ *Tiempos de Llegada*\n"
        texto += "• _'Cuanto tarda [Móvil] en llegar a [Destino]'_: Estimación de tiempo.\n\n"
        
        texto += "🗺️ *Mapas*\n"
        texto += "• _'Mostrar en mapa [Móvil]'_: Abre Google Maps con la posición del móvil.\n"
        texto += "• _'Ver en mapa [Zona]'_: Abre Google Maps con el epicentro de la zona.\n"
        
        audio = "Puedo ayudarte con el estado de la flota, buscar móviles en zonas, calcular tiempos de llegada a destinos, mostrar ubicaciones en Google Maps, o darte la ubicación y recorrido de cualquier vehículo."
        
        return {
            'texto': texto,
            'audio': audio
        }
