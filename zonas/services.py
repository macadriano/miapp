import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def geocode_search(query: str, *, limit: int = 5, ttl: int = 300) -> List[Dict[str, Any]]:
    """
    Realiza una búsqueda de autocompletar usando Nominatim (o el servicio que se
    defina más adelante) y cachea los resultados por TTL segundos.
    """
    query = (query or "").strip()
    if len(query) < 3:
        return []

    cache_key = f"geocode:autocomplete:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": getattr(settings, "WAYGPS_GEOCODER_UA", "WayGPS-Geocoder/1.0"),
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=6)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning("Error consultando geocoder: %s", exc)
        return []

    suggestions: List[Dict[str, Any]] = []
    for item in data:
        try:
            lat = float(item.get("lat"))
            lon = float(item.get("lon"))
        except (TypeError, ValueError):
            continue

        suggestions.append(
            {
                "label": item.get("display_name"),
                "address_formatted": item.get("display_name"),
                "coordinates": {"lat": lat, "lon": lon},
                "bounding_box": item.get("boundingbox"),
                "source": "nominatim",
                "importance": item.get("importance"),
                "place_id": str(item.get("place_id")),
                "raw": item,
            }
        )

    cache.set(cache_key, suggestions, ttl)
    return suggestions


def reverse_geocode(lat: float, lon: float, *, ttl: int = 86400) -> Optional[Dict[str, Any]]:
    """
    Realiza geocodificación inversa (reverse geocoding) usando Nominatim.
    Convierte coordenadas (lat, lon) en una dirección.
    
    Args:
        lat: Latitud
        lon: Longitud
        ttl: Tiempo de vida del cache en segundos (default: 1 día)
        
    Returns:
        Dict con 'direccion' (corta) y 'direccion_formateada' (completa), o None si falla
    """
    cache_key = f"geocode:reverse:{lat:.6f}:{lon:.6f}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": str(lat),
        "lon": str(lon),
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,  # Nivel de detalle (18 = máximo detalle)
    }
    
    headers = {
        "User-Agent": getattr(settings, "WAYGPS_GEOCODER_UA", "WayGPS-Geocoder/1.0"),
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=6)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning("Error consultando reverse geocoder: %s", exc)
        return None
    
    if not data or 'error' in data:
        return None
    
    # Extraer dirección formateada completa
    direccion_formateada = data.get("display_name", "")
    
    # Extraer dirección corta (calle + número si está disponible)
    address = data.get("address", {})
    direccion_parts = []
    
    # Prioridad: road + house_number, luego road, luego otros
    if address.get("road"):
        road = address.get("road")
        house_number = address.get("house_number", "")
        if house_number:
            direccion_parts.append(f"{road} {house_number}")
        else:
            direccion_parts.append(road)
    
    # Si no hay road, intentar con otros campos
    if not direccion_parts:
        if address.get("house"):
            direccion_parts.append(address.get("house"))
        elif address.get("building"):
            direccion_parts.append(address.get("building"))
        elif address.get("place"):
            direccion_parts.append(address.get("place"))
    
    # Agregar localidad/ciudad
    if address.get("city") or address.get("town") or address.get("village"):
        ciudad = address.get("city") or address.get("town") or address.get("village")
        if ciudad and ciudad not in direccion_parts:
            direccion_parts.append(ciudad)
    
    direccion = ", ".join(direccion_parts) if direccion_parts else direccion_formateada
    
    result = {
        "direccion": direccion,
        "direccion_formateada": direccion_formateada,
        "raw": data,
    }
    
    cache.set(cache_key, result, ttl)
    return result
