"""
Módulo para vectorización de consultas y comparación de similitud
"""
import re
from typing import Dict, List, Optional

# Dependencias opcionales (no deben romper en dev si no están)
try:
    import numpy as np
    NP_AVAILABLE = True
except Exception:
    NP_AVAILABLE = False
    np = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    print("⚠️ sentence-transformers no está instalado. Usando embeddings placeholder.")

# Configuraciones para evitar intentos de conexión a Hugging Face
import os
# Deshabilitar caché de Hugging Face si no hay internet
os.environ.setdefault('HF_HOME', '')  # No usar caché de Hugging Face


class VectorizadorConsultas:
    """
    Clase para vectorizar consultas y comparar con vectores pre-calculados
    """
    
    # Variable de clase para almacenar el modelo singleton
    _modelo_cache = None
    _modelo_loaded = False
    
    def __init__(self):
        self.modelo = None
        # Usar lazy loading para evitar problemas de conexión al iniciar
        pass
    
    def _cargar_modelo(self):
        """
        Carga el modelo con lazy loading. Solo se carga cuando se necesita.
        Implementa un patrón singleton para evitar cargas múltiples.
        """
        if VectorizadorConsultas._modelo_loaded:
            self.modelo = VectorizadorConsultas._modelo_cache
            return
        
        # Verificar si está activado el modo ligero (sin modelo pesado)
        from decouple import config
        lite_mode = config('SOFIA_LITE_MODE', default=False, cast=bool)
        
        if self.modelo is None and ST_AVAILABLE and not lite_mode:
            try:
                # Intentar cargar desde caché local primero si existe
                import os
                cache_dir = os.path.join(os.getcwd(), '.cache', 'models')
                os.makedirs(cache_dir, exist_ok=True)
                
                print("🔄 Intentando cargar modelo de vectorización...")
                
                # Intentar cargar con timeout reducido y sin conexión
                try:
                    self.modelo = SentenceTransformer(
                        'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                        cache_folder=cache_dir
                    )
                    print("✅ Modelo de vectorización cargado")
                    # Guardar en cache de clase
                    VectorizadorConsultas._modelo_cache = self.modelo
                    VectorizadorConsultas._modelo_loaded = True
                except Exception as e:
                    # Si falla, probar sin caché
                    print(f"⚠️ Error cargando modelo: {e}")
                    print(f"⚠️ Usando embeddings placeholder (sin conexión a internet).")
                    self.modelo = None
                    VectorizadorConsultas._modelo_loaded = True
            except Exception as e:
                print(f"⚠️ Error crítico cargando modelo: {e}")
                print(f"⚠️ Usando embeddings placeholder.")
                self.modelo = None
                VectorizadorConsultas._modelo_loaded = True
        else:
            print("⚠️ sentence-transformers no disponible. Usando embeddings placeholder.")
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto: minúsculas, sin tildes, elimina muletillas/groserías."""
        import unicodedata
        # Minúsculas
        t = text.lower()
        # Quitar tildes
        t = ''.join(
            c for c in unicodedata.normalize('NFD', t)
            if unicodedata.category(c) != 'Mn'
        )
        # Remover palabras basura comunes que no cambian la intención
        stop_extras = {
            'carajo', 'carajos', 'mierda', 'che', 'por', 'favor', 'porfa', 'eh', 'este', 'esta',
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'
        }
        tokens = [tok for tok in t.split() if tok not in stop_extras]
        t = ' '.join(tokens)
        # Colapsar espacios múltiples
        t = ' '.join(t.split())
        return t

    def vectorizar(self, texto: str) -> List[float]:
        """
        Vectoriza un texto de consulta
        
        Args:
            texto: Texto a vectorizar
            
        Returns:
            Lista de floats representando el embedding
        """
        # Intentar cargar el modelo si no está cargado
        if self.modelo is None:
            self._cargar_modelo()
        
        if self.modelo:
            try:
                embedding = self.modelo.encode(self._normalize_text(texto), convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                print(f"⚠️ Error en vectorización: {e}")
                return self._placeholder_embedding(texto)
        else:
            return self._placeholder_embedding(self._normalize_text(texto))
    
    def _placeholder_embedding(self, texto: str) -> List[float]:
        """
        Genera un embedding placeholder basado en hash del texto
        Para desarrollo cuando no hay modelo cargado
        IMPORTANTE: Debe ser consistente con la función del management command
        """
        size = 384
        seed = hash(texto.lower().strip()) % (2**31)
        import random
        rnd = random.Random(seed)
        return [rnd.random() for _ in range(size)]
    
    def calcular_similitud(self, vector1: List[float], vector2: List[float]) -> float:
        """
        Calcula similitud coseno entre dos vectores
        
        Args:
            vector1: Primer vector
            vector2: Segundo vector
            
        Returns:
            Valor de similitud entre 0 y 1
        """
        try:
            # Protección por longitud
            if not vector1 or not vector2:
                return 0.0
            if len(vector1) != len(vector2):
                # Ajustar a la longitud mínima común
                n = min(len(vector1), len(vector2))
                vector1 = vector1[:n]
                vector2 = vector2[:n]

            if NP_AVAILABLE:
                v1 = np.array(vector1)
                v2 = np.array(vector2)
                denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
                if denom == 0:
                    return 0.0
                sim = float(np.dot(v1, v2) / denom)
            else:
                # Fallback sin numpy
                from math import sqrt
                dot = sum(a*b for a, b in zip(vector1, vector2))
                norm1 = sqrt(sum(a*a for a in vector1))
                norm2 = sqrt(sum(b*b for b in vector2))
                denom = norm1 * norm2
                sim = (dot / denom) if denom else 0.0

            return max(0.0, min(1.0, sim))
        except Exception as e:
            print(f"⚠️ Error calculando similitud: {e}")
            return 0.0
    
    def extraer_variables(self, texto: str, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Extrae variables del texto usando expresiones regulares
        
        Args:
            texto: Texto de consulta
            variables: Diccionario con patrones regex para extraer
            
        Returns:
            Diccionario con variables extraídas
        """
        resultado = {}
        
        for nombre, patron in variables.items():
            matches = re.findall(patron, texto, re.IGNORECASE)
            if matches:
                resultado[nombre] = matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        return resultado


class ProcesadorConsultas:
    """
    Procesa consultas de usuarios y genera respuestas
    """
    
    def __init__(self):
        self.vectorizador = VectorizadorConsultas()
    
    def procesar_consulta(self, texto: str, vectores_db: List) -> Optional[Dict]:
        """
        Procesa una consulta y encuentra el vector más similar
        
        Args:
            texto: Consulta del usuario
            vectores_db: Lista de VectoresConsulta de la BD
            
        Returns:
            Diccionario con información del vector más similar o None
        """
        if not vectores_db:
            return None
        
        # Vectorizar la consulta del usuario
        vector_consulta = self.vectorizador.vectorizar(texto.lower())
        
        mejor_match = None
        mejor_similitud = 0.0
        
        # Comparar con cada vector de la BD
        for vector_db in vectores_db:
            if not vector_db.activo or not vector_db.vector_embedding:
                continue
            
            # Calcular similitud
            similitud = self.vectorizador.calcular_similitud(
                vector_consulta,
                vector_db.vector_embedding
            )
            
            # Debug: mostrar similitudes
            print(f"   💭 '{vector_db.texto_original}': similitud={similitud:.3f}, threshold={vector_db.threshold}")
            
            # Verificar si supera el threshold
            if similitud >= vector_db.threshold and similitud > mejor_similitud:
                mejor_similitud = similitud
                mejor_match = {
                    'vector': vector_db,
                    'similitud': similitud,
                    'tipo': vector_db.tipo_consulta,
                    'categoria': vector_db.categoria
                }
        
        if mejor_match:
            # Extraer variables del texto
            variables = self.vectorizador.extraer_variables(
                texto,
                mejor_match['vector'].variables
            )
            mejor_match['variables'] = variables
            
            return mejor_match
        
        return None

