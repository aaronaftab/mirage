import pytest
from pathlib import Path
from werkzeug.datastructures import FileStorage
from ...utils import validate_image, save_image, cleanup_old_images
from config import Config

def create_file_storage(file_obj, filename):
    """Helper to create FileStorage objects for testing"""
    return FileStorage(
        stream=file_obj,
        filename=filename,
        content_type="image/png"
    )

def test_validate_image_valid(test_image):
    """Test validation of a valid image"""
    file = create_file_storage(test_image, "test.png")
    is_valid, error = validate_image(file)
    assert is_valid
    assert error == ""

def test_validate_image_no_file():
    """Test validation with no file"""
    is_valid, error = validate_image(None)
    assert not is_valid
    assert "No file provided" in error

def test_validate_image_empty_filename(test_image):
    """Test validation with empty filename"""
    file = create_file_storage(test_image, "")
    is_valid, error = validate_image(file)
    assert not is_valid
    assert "No file provided" in error

def test_validate_image_invalid_extension(test_image):
    """Test validation with unsupported file extension"""
    file = create_file_storage(test_image, "test.gif")
    is_valid, error = validate_image(file)
    assert not is_valid
    assert "Unsupported format" in error

def test_validate_image_empty_file():
    """Test validation with empty file"""
    empty_file = create_file_storage(open(__file__, 'rb'), "test.png")
    is_valid, error = validate_image(empty_file)
    assert not is_valid
    assert "Invalid or corrupted image file" in error

def test_validate_image_corrupt_file(corrupt_image):
    """Test validation with corrupt image data"""
    file = create_file_storage(corrupt_image, "test.png")
    is_valid, error = validate_image(file)
    assert not is_valid
    assert "Invalid or corrupted image file" in error

def test_validate_image_too_large(data_dir):
    """Test validation with file exceeding size limit"""
    large_file = data_dir / 'large.png'
    if not large_file.exists():
        pytest.skip("Test requires large.png in the data directory")
    
    with open(large_file, 'rb') as f:
        file = create_file_storage(f, "large.png")
        is_valid, error = validate_image(file)
        assert not is_valid
        assert "File too large" in error

def test_save_image_success(test_image, app):
    """Test successful image save"""
    with app.app_context():
        file = create_file_storage(test_image, "test.png")
        path = save_image(file)
        assert path.exists()
        assert path.suffix == ".png"
        assert path.parent == Config.UPLOAD_FOLDER

def test_save_image_invalid(corrupt_image, app):
    """Test save with invalid image"""
    with app.app_context():
        file = create_file_storage(corrupt_image, "test.png")
        with pytest.raises(ValueError) as exc_info:
            save_image(file)
        assert "Invalid or corrupted image file" in str(exc_info.value)

def test_cleanup_old_images(app, test_image):
    """Test cleanup of old images"""
    with app.app_context():
        # Save multiple images
        files = []
        for i in range(5):
            file = create_file_storage(test_image, f"test_{i}.png")
            path = save_image(file)
            files.append(path)
        
        # Verify initial count
        assert len(list(Config.UPLOAD_FOLDER.glob("*"))) == 5
        
        # Clean up
        cleanup_old_images(keep_last=2)
        
        # Verify final count
        remaining = list(Config.UPLOAD_FOLDER.glob("*"))
        assert len(remaining) == 2
        # Verify we kept the most recent files
        assert files[-1] in remaining
        assert files[-2] in remaining 