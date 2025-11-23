"""
Middleware para diagnóstico de performance
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TimingMiddleware(MiddlewareMixin):
    """
    Middleware que registra el tiempo de respuesta de cada request
    """
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Solo loggear requests que tardan más de 1 segundo
            if duration > 1.0:
                logger.warning(
                    f"⏱️ SLOW REQUEST: {request.method} {request.path} - "
                    f"{duration:.2f}s - Status: {response.status_code}"
                )
            elif duration > 0.5:
                logger.info(
                    f"⏱️ Request: {request.method} {request.path} - "
                    f"{duration:.2f}s"
                )
            
            # Agregar header de timing
            response['X-Response-Time'] = f"{duration:.3f}"
        
        return response

