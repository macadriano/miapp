# Sistema de matching simple por palabras clave para Sofia

"""Matching logic for Sofia assistant.

Provides:
- Text normalization
- Simple keyword matcher
- Mobile ID extraction
- Destination extraction for proximity queries
- Query processing with variable extraction
"""

from typing import Dict, List, Optional, Tuple
import re
import unicodedata


def normalizar_texto(texto: str, mayusculas: bool = True) -> str:
    """Normaliza texto removiendo tildes y signos raros.
    """
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
    """Matcher simple basado en palabras clave"""

    def __init__(self):
        self.patrones = {
            'POSICION': [
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
                r'envi(a|ar).*whatsapp',
                r'compart(e|ir).*whatsapp',
                r'mand(a|ar).*whatsapp',
                r'pas(a|ar).*whatsapp',
                r'whatsapp.*ubicaci(o|ó)n',
                r'whatsapp.*posici(o|ó)n',
                r'por\s+whatsapp',
                r'por\s+wsp',
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
                r'd(ó|o)nde\s+est(a|á)\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+queda\s+(?:la\s+)?zona',
                r'ubicaci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'direcci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'domicilio\s+de\s+(?:la\s+)?zona',
                r'cu(a|á)l\s+es\s+la\s+direcci(o|ó)n\s+de\s+(?:la\s+)?zona',
                r'cu(a|á)l\s+es\s+el\s+domicilio\s+de\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+se\s+encuentra\s+(?:la\s+)?zona',
                r'd(ó|o)nde\s+se\s+ubica\s+(?:la\s+)?zona',
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
            ],
            'LISTADO_ACTIVOS': [
                r'listado',
                r'lista\s+de\s+m[oó]viles?\s+activ[oa]s?',
                r'quienes?\s+est[aá]n?\s+conectad[oa]s?',
                r'quienes?\s+reportaron',
                r'm[oó]viles?\s+activ[oa]s?',
                r'quienes?\s+est[aá]n?\s+activ[oa]s?',
                r'quienes?\s+est[aá]n?\s+en\s+linea',
            ],
            'SITUACION_FLOTA': [
                r'situaci[oó]n\s+(?:de\s+(?:la\s+)?)?flota',
                r'situaci[oó]n\s+flota',
                r'estado\s+(?:de\s+(?:la\s+)?)?flota',
                r'resumen\s+(?:de\s+)?flota',
                r'cuantos?\s+est[aá]n?\s+circulando',
                r'cuantos?\s+est[aá]n?\s+detenid[oa]s?',
                r'm[oó]viles?\s+detenid[oa]s?',
                r'm[oó]viles?\s+circulando',
                r'estado\s+operativo',
                r'decime\s+los\s+m[oó]viles?\s+detenid[oa]s?',
                r'decime\s+los\s+m[oó]viles?\s+circulando',
                r'cuales?\s+son\s+los?\s+m[oó]viles?\s+detenid[oa]s?',
                r'cuales?\s+son\s+los?\s+m[oó]viles?\s+circulando',
            ],
            'MOVILES_EN_ZONA': [
                r'm[oó]viles?\s+en\s+zona',
                r'quienes?\s+est[aá]n?\s+en\s+(?:la\s+)?zona',
                r'quien\s+est[aá]\s+en\s+(?:la\s+)?zona',
                r'm[oó]viles?\s+dentro\s+de\s+(?:la\s+)?zona',
                r'quienes?\s+est[aá]n?\s+en\s+el\s+dep[oó]sito',
                r'quienes?\s+est[aá]n?\s+en\s+el\s+almac[eé]n',
            ],
            'MOVILES_FUERA_DE_ZONA': [
                r'm[oó]viles?\s+fuera\s+de\s+(?:la\s+)?zona',
                r'm[oó]viles?\s+afuera\s+de\s+(?:la\s+)?zona',
                r'veh[ií]culos?\s+fuera\s+de\s+(?:la\s+)?zona',
                r'veh[ií]culos?\s+afuera\s+de\s+(?:la\s+)?zona',
                r'que\s+(?:m[oó]viles?|veh[ií]culos?)\s+est[aá]n?\s+fuera\s+de',
                r'que\s+(?:m[oó]viles?|veh[ií]culos?)\s+est[aá]n?\s+afuera\s+de',
                r'que\s+veh[ií]culo\s+est[aá]n?\s+fuera\s+de',
                r'que\s+veh[ií]culo\s+est[aá]n?\s+afuera\s+de',
                r'quienes?\s+est[aá]n?\s+fuera\s+de\s+(?:la\s+)?zona',
                r'quienes?\s+est[aá]n?\s+afuera\s+de\s+(?:la\s+)?zona',
                r'm[oó]viles?\s+que\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona',
                r'veh[ií]culos?\s+que\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona',
                r'que\s+(?:m[oó]viles?|veh[ií]culos?)\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona',
                r'quienes?\s+no\s+est[aá]n?\s+en\s+(?:la\s+)?zona',
                r'm[oó]viles?\s+fuera\s+del\s+dep[oó]sito',
                r'm[oó]viles?\s+fuera\s+del\s+almac[eé]n',
                r'cuales?\s+salieron\s+de',
                r'quienes?\s+salieron\s+de',
                r'quien\s+salio\s+de',
                r'quien\s+sali[oó]\s+de',
            ],
            'INGRESO_A_ZONA': [
                r'ingreso\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'ingreso\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'ingres[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'ingres[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'entr[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'entr[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'entro\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'entro\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'entrada\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'entrada\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+ingres[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+ingreso\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+entr[oó]\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+entrada\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'a\s+que\s+hora\s+(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'en\s+que\s+momento\s+(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                # Patrones con orden diferente: "entro el movil X a zona Y"
                r'(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'a\s+que\s+hora\s+(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
                r'en\s+que\s+momento\s+(?:ingres[oó]|ingreso|entr[oó]|entro|entrada)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+(?:a|al|a\s+la)\s+(?:la\s+)?zona',
            ],
            'SALIO_DE_ZONA': [
                r'sali[oó]\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'sali[oó]\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'salido\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'salido\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'salida\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'salida\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+sali[oó]\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+salido\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+salida\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+se\s+sali[oó]\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+se\s+salio\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'a\s+que\s+hora\s+(?:sali[oó]|salido|salida|se\s+sali[oó])\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                r'en\s+que\s+momento\s+(?:sali[oó]|salido|salida|se\s+sali[oó])\s+(?:de|del|de\s+la)\s+(?:la\s+)?zona',
                # Patrones con orden diferente: "salió el movil X de zona Y"
                r'sali[oó]\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+sali[oó]\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona',
                r'a\s+que\s+hora\s+(?:sali[oó]|salido)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona',
                r'en\s+que\s+momento\s+(?:sali[oó]|salido)\s+(?:el\s+)?(?:movil|móvil|vehiculo|vehículo|camion|camión|auto)\s+\w+\s+de\s+(?:la\s+)?zona',
            ],
            'PASO_POR_ZONA': [
                r'pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'paso\s+(?:por|por\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'paso\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'pas[oó]\s+(?:por|por\s+la)\s+(?:el|la)\s+(?:dep[oó]sito|almac[eé]n|zona)',
                r'cu[aá]ndo\s+pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'cu[aá]ndo\s+paso\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'a\s+que\s+hora\s+pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'en\s+que\s+momento\s+pas[oó]\s+(?:por|por\s+la)\s+(?:la\s+)?zona',
                r'estuvo\s+(?:en|en\s+la)\s+(?:la\s+)?zona\s+\w+',
                r'estuvo\s+(?:en|en\s+la)\s+(?:la\s+)?zona',
                r'estuvo\s+(?:en|en\s+el)\s+(?:dep[oó]sito|almac[eé]n)',
            ],
            'AYUDA_GENERAL': [
                r'ayuda',
                r'que\s+puedes?\s+hacer',
                r'que\s+sabes?\s+hacer',
                r'lista\s+de\s+comandos',
                r'ayuda\s+con\s+comandos',
                r'comandos\s+disponibles',
                r'que\s+comandos\s+hay',
                r'como\s+te\s+uso',
                r'que\s+haces',
            ],
            'VER_MAPA': [
                r'mostrar\s+en\s+mapa',
                r'ver\s+en\s+mapa',
                r'mostrar\s+en\s+google',
                r'ver\s+en\s+google',
                r'abrir\s+mapa',
                r'abrir\s+google\s+map',
                r'mapa\s+de',
            ],
        }

    def buscar_patron(self, texto: str, tipo: str) -> bool:
        """Verifica si el texto coincide con algún patrón del tipo"""
        if tipo not in self.patrones:
            return False
        texto_normalizado = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        texto_lower = texto_normalizado.lower()
        for patron in self.patrones[tipo]:
            if re.search(patron, texto, re.IGNORECASE) or re.search(patron, texto_normalizado, re.IGNORECASE):
                return True
        # Heurísticas adicionales para MOVILES_FUERA_DE_ZONA
        if tipo == 'MOVILES_FUERA_DE_ZONA':
            # Detectar "que vehiculos/moviles" + "fuera/afuera/no estan" sin requerir "zona"
            tiene_vehiculos = re.search(r'\b(?:veh[ií]culos?|m[oó]viles?)\b', texto_lower, re.IGNORECASE)
            tiene_fuera = re.search(r'\b(?:fuera|afuera|salieron?|sali[oó])\s+de\b', texto_lower, re.IGNORECASE)
            tiene_no_estan = re.search(r'\bno\s+est[aá]n?\s+en\b', texto_lower, re.IGNORECASE)
            tiene_que = re.search(r'\bque\s+(?:veh[ií]culos?|m[oó]viles?)\b', texto_lower, re.IGNORECASE)
            # Si tiene "que vehiculos/moviles" y "fuera/no estan", es MOVILES_FUERA_DE_ZONA
            if tiene_vehiculos and (tiene_fuera or tiene_no_estan):
                return True
            # Si tiene "que vehiculos/moviles" y "fuera de" o "afuera de"
            if tiene_que and tiene_fuera:
                return True
        if tipo == 'CERCANIA':
            keywords = ['cerca', 'distancia', 'cuanto esta', 'cuanto tarda', 'cuanto demora', 'tiempo']
            if any(kw in texto_lower for kw in keywords):
                return True
        return False

    def extraer_movil(self, texto: str, exclude: Optional[List[str]] = None) -> Optional[str]:
        """Extrae el identificador del móvil del texto"""
        exclude = set(exclude or [])
        patrones_movil = [
            # Patente formato "letras-números-letras" (ej: AA285TA, JGI640)
            (r'\b([A-Z]{2,3})\s*(\d{2,4})\s*([A-Z]{1,3})\b', lambda m: m.group(1) + m.group(2) + m.group(3)),
            # Patente formato "letras-números" (ej: ASN773, OVV799)
            (r'\b([A-Z]{2,5}\d{2,4})\b', lambda m: m.group(1)),
            (r'\b([A-Z]{2,5})\s*(\d{2,4})\b', lambda m: m.group(1) + m.group(2)),
            # Patente formato "números-letras-números" (menos común)
            (r'\b(\d{1,3})\s*([A-Z]{2,3})\s*(\d{1,3})\b', lambda m: m.group(1) + m.group(2) + m.group(3)),
            # Nombres específicos (CAMION5, MOVIL3, etc.)
            (r'\b(?:CAMION|CAMIÓN|MOVIL|MÓVIL|VEHICULO|VEHÍCULO)\s*(\d{1,4})\b', lambda m: re.sub(r'\s+', '', m.group(0))),
            # Patrón genérico (fallback)
            (r'\b([A-Z]+)\s*(\d{1,4})\b', lambda m: m.group(1) + m.group(2)),
            (r'\b([A-Z]+\d{1,4})\b', lambda m: m.group(1)),
        ]
        texto_normalizado = normalizar_texto(texto, mayusculas=True)
        numeros_map = {
            'CERO': '0', 'UNO': '1', 'UN': '1', 'UNA': '1',
            'DOS': '2', 'TRES': '3', 'CUATRO': '4', 'CINCO': '5',
            'SEIS': '6', 'SIETE': '7', 'OCHO': '8', 'NUEVE': '9',
            'DIEZ': '10', 'ONCE': '11', 'DOCE': '12', 'TRECE': '13',
            'CATORCE': '14', 'QUINCE': '15', 'DIECISEIS': '16', 'DIECISÉIS': '16',
            'DIECISIETE': '17', 'DIECIOCHO': '18', 'DIECINUEVE': '19', 'VEINTE': '20',
        }
        def reemplazar_palabra(match):
            return numeros_map.get(match.group(0), match.group(0))
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

    def extraer_destino(self, texto: str, exclude: Optional[List[str]] = None) -> Optional[str]:
        """Extrae el destino usando la lógica de cercanía"""
        destino, _, _ = extraer_destino_cercania(texto)
        if destino and exclude:
            if isinstance(exclude, (list, set)) and destino in exclude:
                return None
        return destino


class ProcesadorSimple:
    """Procesador simple que usa matching por palabras clave"""

    def __init__(self):
        self.matcher = SimpleMatcher()

    def procesar_consulta(self, texto: str, vectores_db: List) -> Optional[Dict]:
        """Procesa una consulta usando matching simple"""
        texto_lower = texto.lower()
        # Detectar tipos posibles
        tipos_detectados = []
        for tipo in ['POSICION', 'RECORRIDO', 'COMANDO_WHATSAPP', 'LLEGADA', 'CERCANIA', 'UBICACION_ZONA', 'SALUDO', 
                     'LISTADO_ACTIVOS', 'SITUACION_FLOTA', 'MOVILES_EN_ZONA', 'MOVILES_FUERA_DE_ZONA', 
                     'INGRESO_A_ZONA', 'SALIO_DE_ZONA', 'PASO_POR_ZONA', 'AYUDA_GENERAL', 'VER_MAPA']:
            if self.matcher.buscar_patron(texto, tipo):
                tipos_detectados.append(tipo)
        # Variables auxiliares
        tiene_palabra_zona = re.search(r'\b(?:zona|dep(o|ó)sito|almac(e|é)n|base|sede|oficina|planta)\b', texto_lower, re.IGNORECASE)
        tiene_palabra_whatsapp = re.search(r'\b(?:whatsapp|wsp|wapp|envi[aá]|compart[eí]|mand[aá]|pas[aá])\b', texto_lower, re.IGNORECASE)
        tiene_movil = self.matcher.extraer_movil(texto) is not None
        tiene_palabra_cercania = re.search(r'\b(?:cerca|cercano|distancia|proximo|próximo)\b', texto_lower, re.IGNORECASE)
        print(f"  Tipos detectados: {tipos_detectados}")
        print(f"  tiene_movil={tiene_movil}, tiene_zona={bool(tiene_palabra_zona)}, tiene_whatsapp={bool(tiene_palabra_whatsapp)}, tiene_cercania={bool(tiene_palabra_cercania)}")
        # Detectar palabras clave de "fuera de zona" sin requerir la palabra "zona" explícita
        tiene_fuera_afuera = re.search(r'\b(?:fuera|afuera|salieron?|sali[oó])\s+de\b', texto_lower, re.IGNORECASE)
        tiene_no_estan = re.search(r'\bno\s+est[aá]n?\s+en\b', texto_lower, re.IGNORECASE)
        tiene_vehiculos_moviles = re.search(r'\b(?:veh[ií]culos?|m[oó]viles?)\b', texto_lower, re.IGNORECASE)
        
        # Priorizar según reglas
        tipo_seleccionado = None
        # Prioridad alta: comandos específicos y ayuda
        if 'AYUDA_GENERAL' in tipos_detectados:
            tipo_seleccionado = 'AYUDA_GENERAL'
            print("  → Seleccionado: AYUDA_GENERAL")
        elif 'LISTADO_ACTIVOS' in tipos_detectados:
            tipo_seleccionado = 'LISTADO_ACTIVOS'
            print("  → Seleccionado: LISTADO_ACTIVOS")
        elif 'SITUACION_FLOTA' in tipos_detectados:
            tipo_seleccionado = 'SITUACION_FLOTA'
            print("  → Seleccionado: SITUACION_FLOTA")
        elif 'MOVILES_FUERA_DE_ZONA' in tipos_detectados:
            # Priorizar MOVILES_FUERA_DE_ZONA si está detectado (con o sin palabra "zona" explícita)
            tipo_seleccionado = 'MOVILES_FUERA_DE_ZONA'
            print("  → Seleccionado: MOVILES_FUERA_DE_ZONA")
        elif (tiene_fuera_afuera or tiene_no_estan) and tiene_vehiculos_moviles:
            # Detectar "fuera de" o "no están en" con "vehículos" o "móviles" aunque no haya patrón exacto
            tipo_seleccionado = 'MOVILES_FUERA_DE_ZONA'
            print("  → Seleccionado: MOVILES_FUERA_DE_ZONA (heurística: fuera/no están + vehículos)")
        elif 'INGRESO_A_ZONA' in tipos_detectados:
            tipo_seleccionado = 'INGRESO_A_ZONA'
            print("  → Seleccionado: INGRESO_A_ZONA")
        elif 'SALIO_DE_ZONA' in tipos_detectados:
            tipo_seleccionado = 'SALIO_DE_ZONA'
            print("  → Seleccionado: SALIO_DE_ZONA")
        elif 'PASO_POR_ZONA' in tipos_detectados:
            tipo_seleccionado = 'PASO_POR_ZONA'
            print("  → Seleccionado: PASO_POR_ZONA")
        elif 'MOVILES_EN_ZONA' in tipos_detectados and tiene_palabra_zona:
            tipo_seleccionado = 'MOVILES_EN_ZONA'
            print("  → Seleccionado: MOVILES_EN_ZONA (tiene palabra zona)")
        elif 'VER_MAPA' in tipos_detectados:
            tipo_seleccionado = 'VER_MAPA'
            print("  → Seleccionado: VER_MAPA")
        elif 'UBICACION_ZONA' in tipos_detectados and tiene_palabra_zona:
            tipo_seleccionado = 'UBICACION_ZONA'
            print("  → Seleccionado: UBICACION_ZONA (tiene palabra zona)")
        elif 'POSICION' in tipos_detectados and tiene_movil and not tiene_palabra_cercania:
            tipo_seleccionado = 'POSICION'
            print("  → Seleccionado: POSICION (tiene móvil, sin cercanía)")
        elif 'COMANDO_WHATSAPP' in tipos_detectados and tiene_palabra_whatsapp:
            tipo_seleccionado = 'COMANDO_WHATSAPP'
            print("  → Seleccionado: COMANDO_WHATSAPP (tiene keyword whatsapp)")
        elif 'LLEGADA' in tipos_detectados:
            tipo_seleccionado = 'LLEGADA'
            print("  → Seleccionado: LLEGADA")
            if 'CERCANIA' in tipos_detectados:
                print("  ⚠️ Se detectaron ambos LLEGADA y CERCANIA, priorizando LLEGADA")
        elif 'CERCANIA' in tipos_detectados:
            tipo_seleccionado = 'CERCANIA'
            print("  → Seleccionado: CERCANIA")
        elif 'POSICION' in tipos_detectados:
            tipo_seleccionado = 'POSICION'
            print("  → Seleccionado: POSICION (fallback)")
        elif 'RECORRIDO' in tipos_detectados:
            tipo_seleccionado = 'RECORRIDO'
            print("  → Seleccionado: RECORRIDO")
        elif 'SALUDO' in tipos_detectados:
            tipo_seleccionado = 'SALUDO'
            print("  → Seleccionado: SALUDO")
        # Buscar vector y extraer variables
        if tipo_seleccionado:
            variables: Dict[str, str] = {}
            movil_extraido = self.matcher.extraer_movil(texto)
            if movil_extraido:
                variables['movil'] = movil_extraido
                print(f"  ✅ Móvil extraído: {movil_extraido}")
            if tipo_seleccionado in ['LLEGADA', 'CERCANIA']:
                destino = self.matcher.extraer_destino(texto, exclude=[movil_extraido] if movil_extraido else [])
                if destino:
                    variables['destino'] = destino
                    print(f"  ✅ Destino extraído: {destino}")
            # Buscar vector en la BD
            vector_encontrado = None
            for vector_db in vectores_db:
                if vector_db.tipo_consulta == tipo_seleccionado and vector_db.activo:
                    vector_encontrado = vector_db
                    break
            
            # Si encontramos un vector, usarlo
            if vector_encontrado:
                return {
                    'vector': vector_encontrado,
                    'similitud': 0.85,
                    'tipo': tipo_seleccionado,
                    'categoria': vector_encontrado.categoria,
                    'variables': variables,
                }
            # Si no hay vector en BD pero detectamos el tipo, devolver resultado sin vector
            # (el código en views.py puede manejar esto creando un vector temporal o usando None)
            elif tipo_seleccionado in ['AYUDA_GENERAL', 'LISTADO_ACTIVOS', 'SITUACION_FLOTA', 'MOVILES_EN_ZONA', 'MOVILES_FUERA_DE_ZONA', 
                                       'INGRESO_A_ZONA', 'SALIO_DE_ZONA', 'PASO_POR_ZONA', 'VER_MAPA']:
                # Para estos tipos nuevos, podemos devolver resultado sin vector si no existe en BD
                # El código en views.py deberá manejar el caso de vector_usado = None
                print(f"  ⚠️ Tipo '{tipo_seleccionado}' detectado pero no hay vector en BD, devolviendo resultado directo")
                return {
                    'vector': None,  # Sin vector en BD
                    'similitud': 0.85,
                    'tipo': tipo_seleccionado,
                    'categoria': 'ayuda' if tipo_seleccionado == 'AYUDA_GENERAL' else 'actual',
                    'variables': variables,
                }
        # Heurística para móvil solo
        movil = self.matcher.extraer_movil(texto)
        tokens = texto.strip().split()
        if movil and len(tokens) <= 4:
            for vector_db in vectores_db:
                if vector_db.tipo_consulta == 'POSICION' and vector_db.activo:
                    return {
                        'vector': vector_db,
                        'similitud': 0.80,
                        'tipo': 'POSICION',
                        'categoria': vector_db.categoria,
                        'variables': {'movil': movil},
                    }
        return None

    def extraer_variables(self, texto: str, variables: Dict[str, str]) -> Dict[str, str]:
        """Extrae variables del texto (legacy helper)"""
        resultado: Dict[str, str] = {}
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


def extraer_destino_cercania(texto: str) -> Tuple[Optional[str], Optional[str], bool]:
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
