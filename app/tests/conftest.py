import pytest
from pathlib import Path
import tempfile
import shutil
import io
from flask import Flask
from .. import create_app
from config import Config

class TestConfig(Config):
    TESTING = True
    # Use temporary directories for testing
    UPLOAD_FOLDER = Path(tempfile.mkdtemp()) / 'test_images'
    LOG_FILE = Path(tempfile.mkdtemp()) / 'test.log'
    # Test limits
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
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
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / 'test_data'

@pytest.fixture
def test_image(test_data_dir):
    """Load a valid test image for the e-ink display"""
    image_path = test_data_dir / 'valid.jpg'
    if not image_path.exists():
        pytest.skip("Test requires valid.jpg (480x800) in test_data directory")
    with open(image_path, 'rb') as f:
        return io.BytesIO(f.read())

@pytest.fixture
def corrupt_image():
    """Create a corrupt image file."""
    data = b'Not a valid image file'
    return io.BytesIO(data)

@pytest.fixture
def large_image(test_data_dir):
    """Load a test image that exceeds MAX_CONTENT_LENGTH"""
    image_path = test_data_dir / 'large.jpg'
    if not image_path.exists():
        pytest.skip("Test requires large.jpg (>5MB) in test_data directory")
    with open(image_path, 'rb') as f:
        return io.BytesIO(f.read()) 