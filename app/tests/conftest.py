import pytest
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import io
from flask import Flask
from .. import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    # Use temporary directories for testing
    UPLOAD_FOLDER = Path(tempfile.mkdtemp()) / 'test_images'
    LOG_FILE = Path(tempfile.mkdtemp()) / 'test.log'
    # Smaller limits for testing
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB
    KEEP_IMAGES = 3
    METRICS_INTERVAL = 10

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)
    yield app
    # Cleanup after tests
    shutil.rmtree(TestConfig.UPLOAD_FOLDER.parent, ignore_errors=True)
    shutil.rmtree(TestConfig.LOG_FILE.parent, ignore_errors=True)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def test_image():
    """Create a small test image for basic testing."""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@pytest.fixture
def corrupt_image():
    """Create a corrupt image file."""
    data = b'Not a valid image file'
    return io.BytesIO(data)

@pytest.fixture
def data_dir():
    """Path to the test data directory."""
    return Path(__file__).parent / 'data' 