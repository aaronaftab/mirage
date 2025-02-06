# app/__init__.py
from flask import Flask
from config import Config
from app.display import Display
from app.system_monitor import SystemMonitor

display = Display()
system_monitor = SystemMonitor()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app
