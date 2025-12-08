"""
Módulo para gestionar logs de receptores GPS con rotación automática
"""

import os
import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import gzip
import shutil
from django.conf import settings


class ReceptorLogger:
    """Logger específico para un receptor con rotación automática"""
    
    def __init__(self, port: int, transporte: str = 'TCP', max_days: int = 7):
        self.port = port
        self.transporte = transporte
        self.max_days = max_days
        self.logger = None
        self.log_dir = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Configurar el logger con rotación diaria"""
        # Crear directorio específico para este receptor dentro de BASE_DIR/logs
        base_logs_dir = Path(settings.BASE_DIR) / "logs"
        base_logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = base_logs_dir / f"receptor_{self.port}_{self.transporte}"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger
        self.logger = logging.getLogger(f"receptor_{self.port}")
        self.logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers
        if self.logger.handlers:
            return
        
        # Formato de log
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo con rotación diaria
        log_file = self.log_dir / f"receptor_{self.port}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=self.max_days,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"
        
        # Handler para consola (opcional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_connection(self, client_address: str, action: str):
        """Log de conexiones/desconexiones"""
        self.logger.info(f"[CONEXION] {action} desde {client_address}")
    
    def log_data_received(self, client_address: str, data_size: int, hex_data: str = None):
        """Log de datos recibidos"""
        if hex_data:
            # Truncar datos hex si son muy largos
            hex_preview = hex_data[:100] + "..." if len(hex_data) > 100 else hex_data
            self.logger.info(f"[DATOS] {data_size} bytes desde {client_address} - Hex: {hex_preview}")
        else:
            self.logger.info(f"[DATOS] {data_size} bytes desde {client_address}")
    
    def log_parsed_data(self, parsed_data: dict):
        """Log de datos parseados exitosamente"""
        imei = parsed_data.get('imei', 'Unknown')
        lat = parsed_data.get('latitud', 0)
        lon = parsed_data.get('longitud', 0)
        speed = parsed_data.get('velocidad', 0)
        timestamp = parsed_data.get('timestamp', '')
        fecha_gps = parsed_data.get('fecha_gps', '')
        hora_gps = parsed_data.get('hora_gps', '')
        
        # Formatear timestamp para mostrar
        timestamp_str = ''
        if timestamp:
            try:
                from datetime import datetime
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime('%d/%m/%Y %H:%M:%S')
                else:
                    timestamp_str = timestamp.strftime('%d/%m/%Y %H:%M:%S')
            except:
                timestamp_str = str(timestamp)
        
        if timestamp_str:
            self.logger.info(f"[PARSEADO] IMEI: {imei} - Lat: {lat}, Lon: {lon}, Vel: {speed} km/h - GPS: {timestamp_str}")
        else:
            self.logger.info(f"[PARSEADO] IMEI: {imei} - Lat: {lat}, Lon: {lon}, Vel: {speed} km/h")
    
    def log_error(self, error_msg: str, client_address: str = None):
        """Log de errores"""
        if client_address:
            self.logger.error(f"[ERROR] {error_msg} desde {client_address}")
        else:
            self.logger.error(f"[ERROR] {error_msg}")
    
    def log_warning(self, warning_msg: str, client_address: str = None):
        """Log de advertencias"""
        if client_address:
            self.logger.warning(f"[WARNING] {warning_msg} desde {client_address}")
        else:
            self.logger.warning(f"[WARNING] {warning_msg}")
    
    def log_receptor_status(self, status: str, details: str = None):
        """Log de cambios de estado del receptor"""
        if details:
            self.logger.info(f"[ESTADO] {status} - {details}")
        else:
            self.logger.info(f"[ESTADO] {status}")
    
    def compress_old_logs(self):
        """Comprimir logs antiguos para ahorrar espacio"""
        try:
            for log_file in self.log_dir.glob("*.log.*"):
                if not log_file.name.endswith('.gz'):
                    # Comprimir archivo
                    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    # Eliminar archivo original
                    log_file.unlink()
        except Exception as e:
            self.logger.error(f"[ERROR] Error comprimiendo logs: {str(e)}")
    
    def cleanup_old_logs(self):
        """Limpiar logs más antiguos que max_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_days)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    
        except Exception as e:
            self.logger.error(f"[ERROR] Error limpiando logs antiguos: {str(e)}")


class LoggingManager:
    """Gestor central de logs para todos los receptores"""
    
    def __init__(self):
        self.loggers: Dict[int, ReceptorLogger] = {}
        # Usar ruta absoluta basada en BASE_DIR para evitar problemas de cwd
        self.base_log_dir = Path(settings.BASE_DIR) / "logs"
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, port: int, transporte: str = 'TCP') -> ReceptorLogger:
        """Obtener o crear logger para un puerto específico"""
        if port not in self.loggers:
            self.loggers[port] = ReceptorLogger(port, transporte)
        return self.loggers[port]
    
    def get_log_files(self, port: int = None) -> list:
        """Obtener lista de archivos de log"""
        log_files = []
        
        if port:
            # Logs de un puerto específico
            # 1) Nueva convención: logs dentro de subcarpetas receptor_{port}_TCP / receptor_{port}_UDP
            for dir_path in self.base_log_dir.glob(f"receptor_{port}_*"):
                if dir_path.is_dir():
                    log_files.extend(dir_path.glob("*.log*"))

            # 2) Convención antigua/alternativa: archivos directamente bajo BASE_DIR/logs
            log_files.extend(self.base_log_dir.glob(f"receptor_{port}.log*"))
        else:
            # Todos los logs
            # 1) Logs en subcarpetas receptor_{port}_TCP / receptor_{port}_UDP
            for receptor_dir in self.base_log_dir.glob("receptor_*"):
                if receptor_dir.is_dir():
                    log_files.extend(receptor_dir.glob("*.log*"))

            # 2) Logs directamente en BASE_DIR/logs (compatibilidad hacia atrás)
            log_files.extend(self.base_log_dir.glob("receptor_*.log*"))
        
        # Ordenar por fecha de modificación (más recientes primero)
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files
    
    def get_log_content(self, log_file_path: str, lines: int = 100) -> str:
        """Obtener contenido de un archivo de log"""
        try:
            log_path = Path(log_file_path)
            
            if not log_path.exists():
                return "Archivo de log no encontrado"
            
            # Manejar archivos comprimidos
            if log_path.suffix == '.gz':
                with gzip.open(log_path, 'rt', encoding='utf-8') as f:
                    content_lines = f.readlines()
            else:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content_lines = f.readlines()
            
            # Retornar las últimas N líneas
            return ''.join(content_lines[-lines:])
            
        except Exception as e:
            return f"Error leyendo log: {str(e)}"
    
    def cleanup_all_logs(self):
        """Limpiar logs antiguos de todos los receptores"""
        for logger in self.loggers.values():
            logger.cleanup_old_logs()
            logger.compress_old_logs()


# Instancia global del gestor de logs
logging_manager = LoggingManager()
