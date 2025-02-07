from pathlib import Path
import os
from typing import List

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this'
    ENV = 'production'
    DEBUG = False
    
    # File upload settings
    UPLOAD_FOLDER = Path(__file__).parent / 'instance' / 'images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    KEEP_IMAGES = int(os.environ.get('KEEP_IMAGES', '5'))
    
    # Display settings
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg']
    METRICS_INTERVAL = int(os.environ.get('METRICS_INTERVAL', '300'))  # 5 minutes
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_FILE = Path(__file__).parent / 'logs' / 'mirage.log'
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', '10240'))  # 10KB per file
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '10'))
    
    # Optional API authentication
    API_TOKEN = os.environ.get('API_TOKEN')  # If set, will require token auth
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of any errors"""
        errors = []
        
        # Check upload folder
        try:
            cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create upload folder: {e}")
        
        # Check log folder
        try:
            cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log folder: {e}")
        
        # Validate numeric values
        if cls.METRICS_INTERVAL < 10:
            errors.append("METRICS_INTERVAL must be >= 10 seconds")
            
        if cls.MAX_CONTENT_LENGTH < 1024:
            errors.append("MAX_CONTENT_LENGTH must be >= 1024 bytes")
            
        if cls.KEEP_IMAGES < 1:
            errors.append("KEEP_IMAGES must be >= 1")
            
        if cls.LOG_MAX_BYTES < 1024:
            errors.append("LOG_MAX_BYTES must be >= 1024 bytes")
            
        if cls.LOG_BACKUP_COUNT < 1:
            errors.append("LOG_BACKUP_COUNT must be >= 1")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL.upper() not in valid_levels:
            errors.append(f"LOG_LEVEL must be one of: {valid_levels}")
        
        # Warn about development settings
        if 'dev' in cls.SECRET_KEY:
            errors.append("WARNING: Using development SECRET_KEY")
            
        if not cls.API_TOKEN:
            errors.append("WARNING: API authentication is disabled")
        
        return errors
