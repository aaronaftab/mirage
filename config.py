from pathlib import Path
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this'
    UPLOAD_FOLDER = Path(__file__).parent / 'instance' / 'images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ENV = 'production'
    DEBUG = False
