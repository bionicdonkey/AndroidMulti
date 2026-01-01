"""Logging module for the application"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class LogEmitter(QObject):
    """Detached signal emitter for logging"""
    log_message = pyqtSignal(str, str)  # message, level


class QtLogHandler(logging.Handler):
    """
    Custom logging handler that uses a detached QObject emitter.
    This prevents "wrapped C/C++ object deleted" errors during shutdown
    because we check if the emitter still exists before signaling.
    """
    
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.emitter = LogEmitter()
        self._closed = False
    
    def emit(self, record):
        """Emit log record as Qt signal"""
        if self._closed or not self.emitter:
            return
            
        try:
            msg = self.format(record)
            level = record.levelname
            # Check if C++ object still exists
            try:
                self.emitter.log_message.emit(msg, level)
            except (RuntimeError, AttributeError):
                self._closed = True
        except Exception:
            pass
    
    def close(self):
        """Close the handler"""
        self._closed = True
        super().close()


class AppLogger:
    """Application logger singleton"""
    _instance = None
    _logger = None
    _qt_handler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._initialize_logger()
    
    def _initialize_logger(self):
        """Initialize the logger"""
        self._logger = logging.getLogger('AndroidMultiEmulator')
        self._logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self._logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
        
        # File handler
        log_dir = Path.home() / ".android_multi_emulator"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
        
        # Qt handler (for UI integration)
        self._qt_handler = QtLogHandler()
        self._qt_handler.setLevel(logging.INFO)
        self._logger.addHandler(self._qt_handler)
    
    def get_logger(self):
        """Get the logger instance"""
        return self._logger
    
    def get_qt_handler(self) -> Optional[QtLogHandler]:
        """Get the Qt handler for UI integration"""
        return self._qt_handler
    
    def info(self, message: str):
        """Log info message"""
        self._logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self._logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self._logger.error(message)
    
    def exception(self, message: str):
        """Log exception with traceback"""
        self._logger.exception(message)


def get_logger():
    """Get the application logger"""
    return AppLogger().get_logger()
