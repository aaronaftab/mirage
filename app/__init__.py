# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler
import os
import atexit
import sys
from flask import Flask, current_app
from config import Config

def setup_logging(config):
    """Set up logging with file and console handlers"""
    # Ensure log directory exists
    config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Get the log level (convert from string)
    log_level = getattr(logging, config.LOG_LEVEL.upper())
    
    # Remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    
    # Configure handlers
    handlers = [
        # File handler
        RotatingFileHandler(
            str(config.LOG_FILE),
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT
        ),
        # Console handler
        logging.StreamHandler()
    ]
    
    # Set up formatters and levels
    for handler in handlers:
        handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        handler.setLevel(log_level)
        root_logger.addHandler(handler)
    
    # Set overall log level
    root_logger.setLevel(log_level)

def create_app(config_class=Config):
    # Validate configuration
    errors = config_class.validate()
    for error in errors:
        if error.startswith('WARNING'):
            print(f"\033[93m{error}\033[0m", file=sys.stderr)  # Yellow warnings
        else:
            print(f"\033[91m{error}\033[0m", file=sys.stderr)  # Red errors
            if not error.startswith('WARNING'):  # Don't exit on warnings
                sys.exit(1)
    
    # Set up logging first
    setup_logging(config_class)
    logger = logging.getLogger(__name__)
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    logger.info('Mirage startup')
    
    with app.app_context():
        # Import components here to avoid circular imports
        from app.display import Display
        from app.system_monitor import SystemMonitor
        
        # Initialize components
        app.display = Display()
        app.system_monitor = SystemMonitor(
            display=app.display,
            metrics_interval=config_class.METRICS_INTERVAL
        )
        
        # Register cleanup
        atexit.register(app.system_monitor.shutdown)
        
        # Register blueprints
        from app.routes import bp
        app.register_blueprint(bp)
    
    return app
