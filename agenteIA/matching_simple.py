"""
Sistema de matching simple por palabras clave para Sofia
"""
from typing import Dict, List, Optional
import re
import unicodedata


def normalizar_texto(texto: str, mayusculas: bool = True) -> str:
    """Normaliza texto removiendo tildes y signos raros."""
    texto_nfkd = unicodedata.normalize('NFKD', texto)
    texto_sin_tilde = ''.join(
        c for c in texto_nfkd
        if unicodedata.category(c) != 'Mn'
    )
    texto_sin_tilde = (
        texto_sin_tilde
        .replace('¿', ' ')
        .replace('¡', ' ')
        .replace('?', ' ')
    )
    return texto_sin_tilde.upper() if mayusculas else texto_sin_tilde.lower()


class SimpleMatcher:
    """
    Matcher simple basado en palabras clave
    """
    
    def __init__(self):
        self.patrones = {
            'POSICION': [
                # Verbos explícitos
                r'd(ó|o)nde.*est(a|á)',
                r'd(ó|o)nde.*(se\s+encuentra|queda)',
                r'ubicaci(o|ó)n',
                r'posici(o|ó)n',
                r'd(ó|o)nde.*est(a|á).*ahora',
                r'localizaci(o|ó)n',
                r'd(ó|o)nde.*anda',
                # Sin verbo: "donde asn 773" o similares
                r'd(ó|o)nde\s+[a-zA-Z]{2,5}\s*\d{2,5}',
            ],
            'RECORRIDO': [
                r'(qu(e|é)|que).*hic(o|ó)',
                r'd(ó|o)nde.*estuv(o|ó)',
                r'recorrid(o|ó)',
                r'historial',
                r'ayer',
                r'pasado',
                r'a\s+que\s+distancia',
                r'a\s+cu[aá]nt[oa]?\s+tiempo',
                r'cu[aá]nt[oa]?\s+tiempo\s+est[aá]',
            ],
            'SALUDO': [
                r'hola',
                r'buenos\s*(d(i|í)as|tardes|noches)',
                r'buen\s*(d(i|í)a|tarde|noche)',
                r'hi',
            ],
            'COMANDO_WHATSAPP': [
                r'envi(a|ar|ar).*whatsapp',
                r'compart(e|ir).*whatsapp',
                r'envi(a|ar|ar).*ubicaci(o|ó)n',
                r'env(i|í)a.*por.*whatsapp',
            ],
            'LLEGADA': [
                r'llega',
                r'tiempo.*llegada',
                r'cu(á|a)ndo.*lleg(a|ar)',
                r'estimaci(o|ó)n',
                r'cu[aá]nt[oa]?\s+tardar[ií]a?\s+hasta',
                r'cu[aá]nt[oa]?\s+demorar[ií]a?\s+hasta',
                r'cu[aá]nt[oa]?\s+tarda\s+hasta',
                r'cu[aá]nt[oa]?\s+demora\s+hasta',
                r'cu[aá]nt[oa]?\s+tardar[ií]a?\s+en\s+llegar\s+a',
                r'cu[aá]nt[oa]?\s+demorar[ií]a?\s+en\s+llegar\s+a',
                # Patrones específicos para "cuanto tarda a [destino]"
                r'cu[aá]nt[oa]?\s+tarda\s+a\s+',
                r'cu[aá]nt[oa]?\s+tardar[ií]a?\s+a\s+',
                r'cu[aá]nt[oa]?\s+demora\s+a\s+',
                r'cu[aá]nt[oa]?\s+demorar[ií]a?\s+a\s+',
                r'cu[aá]nt[oa]?\s+tiempo\s+tarda\s+(?:en\s+)?llegar\s+a\s+',
                r'cu[aá]nt[oa]?\s+tiempo\s+demora\s+(?:en\s+)?llegar\s+a\s+',
            ],
            'UBICACION_ZONA': [
                # Patrones específicos con la palabra "zona"
                r'd(ó|o)nde\s+est(a|á)\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+queda\s+(?:la\s+)?zona',
                r'ubicaci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'direcci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'domicilio\s+de\s+(?:la\s+)?zona',
                r'cu(a|á)l\s+es\s+la\s+direcci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'cu(a|á)l\s+es\s+el\s+domicilio\s+de\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+se\s+encuentra\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+se\s+ubica\s+(?:la\s+)?zona',
                # Patrones para ubicación/dirección de lugares (depósito, almacén, etc.)
                r'd(ó|o)nde\s+(?:est(a|á)|queda|se\s+encuentra|se\s+ubica)\s+(?:el|la)\s+(?:dep(o|ó)sito|almac(e|é)n|zona|base|sede|oficina|planta)',
                r'ubicaci(o|ó)n\s+(?:del|de\s+la|de)\s+(?:dep(o|ó)sito|almac(e|é)n|zona|base|sede|oficina|planta)',
                r'direcci(o|ó)n\s+(?:del|de\s+la|de)\s+(?:dep(o|ó)sito|almac(e|é)n|zona|base|sede|oficina|planta)',
                r'domicilio\s+(?:del|de\s+la|de)\s+(?:dep(o|ó)sito|almac(e|é)n|zona|base|sede|oficina|planta)',
                r'cu(a|á)l\s+es\s+(?:la\s+)?(?:ubicaci(o|ó)n|direcci(o|ó)n|domicilio)\s+(?:del|de\s+la|de)\s+(?:dep(o|ó)sito|almac(e|é)n|zona|base|sede|oficina|planta)',
            ],
            'CERCANIA': [
                r'cercan[oa]s?',
                r'cerca\s*(de|del|de la|a)',
                r'proxim[oa]s?',
                r'qu[eé]\s+m[oó]vil(es)?\s+est[aá]n?\s+m[aá]s\s+cerca',
                r'cual(es)?\s+son\s+los?\s+m[oó]viles?\s+m[aá]s\s+cercan[oa]s?',
                r'a\s+que\s+distancia\s+est[aá]',
                r'a\s+cu[aá]nt[oa]?\s+tiempo\s+est[aá]',
                r'cu[aá]nt[oa]?\s+tiempo\s+tarda',
                r'cu[aá]nt[oa]?\s+tardar[ií]a?\s+en\s+llegar',
                r'a\s+cu[aá]nto\s+est[aá]\s+de',
                r'en\s+cu[aá]nto\s+est[aá]\s+(?:de|a)',
                r'en\s+cu[aá]nto\s+llegar[aá]\s+a',
                r'cu[aá]nt[oa]?\s+demora\s+en\s+llegar\s+a',
                r'a\s+qu[eé]\s+distancia\s+est[aá]\s+(?:de|a)',
                r'cu[aá]nt[oa]?\s+est[aá]\s+el\s+(camion|vehiculo|movil)\s+\w+\s+(?:de|del|de\s+el)\s+(camion|vehiculo|movil)\s+\w+',
                r'a\s+qu[eé]\s+distancia\s+est[aá]\s+el\s+(camion|vehiculo|movil)\s+\w+\s+(?:de|del|de\s+el)\s+(camion|vehiculo|movil)\s+\w+',
            ]
        }
    
    def buscar_patron(self, texto: str, tipo: str) -> bool:
        """Verifica si el texto coincide con algún patrón del tipo"""
        if tipo not in self.patrones:
            return False
        
        texto_normalizado = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )

        for patron in self.patrones[tipo]:
            if re.search(patron, texto, re.IGNORECASE) or re.search(patron, texto_normalizado, re.IGNORECASE):
                return True

        if tipo == 'CERCANIA':
            texto_lower = texto_normalizado.lower()
            keywords = ['cerca', 'distancia', 'cuanto esta', 'cuanto tarda', 'cuanto demora', 'tiempo']
            if any(kw in texto_lower for kw in keywords):
                return True
        return False
    
    def extraer_movil(self, texto: str, exclude: Optional[List[str]] = None) -> Optional[str]:
        """Extrae el identificador del móvil del texto"""
        exclude = set(exclude or [])
        patrones_movil = [
            (r'\b([A-Z]{2,5}\d{2,4})\b', lambda m: m.group(1)),
            (r'\b([A-Z]{2,5})\s*(\d{2,4})\b', lambda m: m.group(1) + m.group(2)),
            (r'\b(?:CAMION|CAMIÓN|MOVIL|MÓVIL|VEHICULO|VEHÍCULO)\s*(\d{1,4})\b', lambda m: re.sub(r'\s+', '', m.group(0))),
            (r'\b([A-Z]+)\s*(\d{1,4})\b', lambda m: m.group(1) + m.group(2)),
            (r'\b([A-Z]+\d{1,4})\b', lambda m: m.group(1)),
        ]

        texto_normalizado = normalizar_texto(texto, mayusculas=True)

        numeros_map = {
            'CERO': '0',
            'UNO': '1', 'UN': '1', 'UNA': '1',
            'DOS': '2',
            'TRES': '3',
            'CUATRO': '4',
            'CINCO': '5',
            'SEIS': '6',
            'SIETE': '7',
            'OCHO': '8',
            'NUEVE': '9',
            'DIEZ': '10',
            'ONCE': '11',
            'DOCE': '12',
            'TRECE': '13',
            'CATORCE': '14',
            'QUINCE': '15',
            'DIECISEIS': '16', 'DIECISÉIS': '16',
            'DIECISIETE': '17',
            'DIECIOCHO': '18',
            'DIECINUEVE': '19',
            'VEINTE': '20',
        }

        def reemplazar_palabra(match):
            palabra = match.group(0)
            return numeros_map.get(palabra, palabra)

        texto_normalizado = re.sub(
            r'\b(' + '|'.join(numeros_map.keys()) + r')\b',
            reemplazar_palabra,
            texto_normalizado
        )

        for patron, extractor in patrones_movil:
            match = re.search(patron, texto_normalizado, re.IGNORECASE)
            if match:
                candidato = extractor(match).upper()
                candidato = re.sub(r'\s+', '', candidato)
                if candidato not in exclude and len(candidato) >= 3:
                    return candidato

        return None


class ProcesadorSimple:
    """
    Procesador simple que usa matching por palabras clave
    """
    
    def __init__(self):
        self.matcher = SimpleMatcher()
    
    def procesar_consulta(self, texto: str, vectores_db: List) -> Optional[Dict]:
        """
        Procesa una consulta usando matching simple
        
        Args:
            texto: Consulta del usuario
            vectores_db: Lista de VectoresConsulta de la BD
            
        Returns:
            Diccionario con información del vector más similar o None
        """
        texto_lower = texto.lower()
        
        # PRIMERO: Detectar todos los tipos posibles
        tipos_detectados = []
        for tipo in ['POSICION', 'RECORRIDO', 'COMANDO_WHATSAPP', 'LLEGADA', 'CERCANIA', 'UBICACION_ZONA', 'SALUDO']:
            if self.matcher.buscar_patron(texto, tipo):
                tipos_detectados.append(tipo)
        
        # Si se detectaron múltiples tipos, priorizar según orden de importancia
        # Orden de prioridad: COMANDO_WHATSAPP > LLEGADA > CERCANIA > POSICION > UBICACION_ZONA > RECORRIDO > SALUDO
        # UBICACION_ZONA solo se prioriza si hay palabra "zona" explícita en el texto
        tipo_seleccionado = None
        tiene_palabra_zona = re.search(r'\b(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\b', texto_lower, re.IGNORECASE)
        
        if 'COMANDO_WHATSAPP' in tipos_detectados:
            tipo_seleccionado = 'COMANDO_WHATSAPP'
        elif 'LLEGADA' in tipos_detectados:
            tipo_seleccionado = 'LLEGADA'
            if 'CERCANIA' in tipos_detectados:
                print(f"⚠️ Se detectaron ambos LLEGADA y CERCANIA, priorizando LLEGADA")
        elif 'CERCANIA' in tipos_detectados:
            tipo_seleccionado = 'CERCANIA'
        elif 'POSICION' in tipos_detectados:
            tipo_seleccionado = 'POSICION'
        elif 'UBICACION_ZONA' in tipos_detectados and tiene_palabra_zona:
            # Solo priorizar UBICACION_ZONA si hay palabra "zona" explícita
            tipo_seleccionado = 'UBICACION_ZONA'
        elif 'RECORRIDO' in tipos_detectados:
            tipo_seleccionado = 'RECORRIDO'
        elif 'SALUDO' in tipos_detectados:
            tipo_seleccionado = 'SALUDO'
        
        # Buscar vector del tipo seleccionado
        if tipo_seleccionado:
            for vector_db in vectores_db:
                if vector_db.tipo_consulta == tipo_seleccionado and vector_db.activo:
                    return {
                        'vector': vector_db,
                        'similitud': 0.85,  # Similitud alta para indicar match
                        'tipo': tipo_seleccionado,
                        'categoria': vector_db.categoria,
                        'variables': {}
                    }
        
        # Heurística: si el usuario solo menciona un identificador (patente/alias/código)
        # asumimos que está pidiendo la posición actual.
        movil = self.matcher.extraer_movil(texto)
        tokens = texto.strip().split()
        if movil and len(tokens) <= 4:  # Frases muy cortas como "OVV799" o "donde OVV799"
            for vector_db in vectores_db:
                if vector_db.tipo_consulta == 'POSICION' and vector_db.activo:
                    return {
                        'vector': vector_db,
                        'similitud': 0.80,
                        'tipo': 'POSICION',
                        'categoria': vector_db.categoria,
                        'variables': {'movil': movil}
                    }
        
        return None
    
    def extraer_variables(self, texto: str, variables: Dict[str, str]) -> Dict[str, str]:
        """Extrae variables del texto"""
        resultado = {}
        
        # Extraer móvil
        movil = self.matcher.extraer_movil(texto)
        if movil:
            resultado['movil'] = movil
 
        destino, movil_referencia, destino_es_movil = extraer_destino_cercania(texto)
        if destino:
            resultado['destino'] = destino
            if destino == resultado.get('movil'):
                resultado.pop('movil', None)
        if movil_referencia and movil_referencia not in resultado:
            resultado['movil_referencia'] = movil_referencia
        if destino_es_movil:
            resultado['destino_es_movil'] = True
 
        return resultado


def extraer_destino_cercania(texto: str) -> tuple[Optional[str], Optional[str], bool]:
    """Intenta extraer el destino de una consulta de cercanía."""
    texto_normalizado = normalizar_texto(texto, mayusculas=True)
    texto_limpio = normalizar_texto(texto, mayusculas=False)

    mobile_matches: List[str] = []
    for m in re.finditer(r'\b(?:CAMION|MOVIL|VEHICULO)\s*(\d{1,4})\b', texto_normalizado, re.IGNORECASE):
        mobile_id = re.sub(r'\s+', '', m.group(0)).upper()
        if mobile_id not in mobile_matches:
            mobile_matches.append(mobile_id)

    patrones = [
        r'cercan[oa]s?\s*(?:de|del|de la|a)\s+(.+)',
        r'proxim[oa]s?\s*(?:a|de|del|de la)\s+(.+)',
        r'mas\s+cercan[oa]s?\s*(?:a|de|del|de la)?\s*(.+)',
        r'en\s+cuanto\s+esta\s+(?:de|a)\s+(.+)',
        r'en\s+cuanto\s+llegara?\s+a\s+(.+)',
        r'cuanto\s+demora\s+en\s+llegar\s+a\s+(.+)',
        r'cuanto\s+tardar[ií]a?\s+hasta\s+(.+)',
        r'cuanto\s+demorar[ií]a?\s+hasta\s+(.+)',
        r'cuanto\s+tarda\s+hasta\s+(.+)',
        r'cuanto\s+demora\s+hasta\s+(.+)',
        r'cuanto\s+tardar[ií]a?\s+en\s+llegar\s+a\s+(.+)',
        r'cuanto\s+demorar[ií]a?\s+en\s+llegar\s+a\s+(.+)',
        r'a\s+que\s+distancia\s+esta\s+(?:de|a)\s+(.+)',
        r'a\s+cuanto\s+esta\s+(?:de|a)\s+(.+)',
    ]

    for patron in patrones:
        match = re.search(patron, texto_limpio, re.IGNORECASE)
        if match:
            destino = match.group(1).strip(' ?!.')
            if destino:
                destino_normalizado = ''.join(
                    c for c in unicodedata.normalize('NFD', destino)
                    if unicodedata.category(c) != 'Mn'
                )
                if not re.search(r'(camion|movil|vehiculo)\s*\d+', destino_normalizado, re.IGNORECASE):
                    referencia = mobile_matches[0] if mobile_matches else None
                    return destino, referencia, False

    # Patrones específicos: "a cuanto está el camión 5 de Burzaco"
    if mobile_matches:
        match = re.search(
            r'(?:camion|movil|vehiculo)\s*\d+\s+(?:de|del|desde)\s+(.+)',
            texto_limpio,
            re.IGNORECASE
        )
        if match:
            destino = match.group(1).strip(' ?!.')
            if destino and not re.search(r'(camion|movil|vehiculo)\s*\d+', destino, re.IGNORECASE):
                return destino, mobile_matches[0], False

    if len(mobile_matches) >= 2:
        return mobile_matches[1], mobile_matches[0], True
    if len(mobile_matches) == 1:
        return None, mobile_matches[0], False

    return None, None, False

