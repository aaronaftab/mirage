from pathlib import Path
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config
import os
from PIL import Image
import io

logger = logging.getLogger(__name__)

def validate_image(file) -> tuple[bool, str]:
    """
    Validate image file before saving
    Returns (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file provided"
        
    # Check file extension
    extension = Path(file.filename).suffix.lower()
    if extension not in Config.SUPPORTED_FORMATS:
        return False, f"Unsupported format '{extension}'. Supported formats: {Config.SUPPORTED_FORMATS}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if size > Config.MAX_CONTENT_LENGTH:
        return False, f"File too large ({size} bytes). Maximum size: {Config.MAX_CONTENT_LENGTH} bytes"
    
    if size == 0:
        return False, "File is empty"
    
    # Validate image integrity and dimensions
    try:
        image_bytes = file.read()
        file.seek(0)  # Reset file pointer after reading
        
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Basic integrity check by attempting to load the image
            img.verify()
            
            # Re-open for additional checks (verify() closes the file)
            img = Image.open(io.BytesIO(image_bytes))
            
            # Check image mode (convert if necessary)
            if img.mode not in ('RGB', 'L'):
                logger.warning(f"Image mode '{img.mode}' will be converted to RGB")
            
            # Log image details
            logger.info(f"Image validation - Format: {img.format}, Mode: {img.mode}, Size: {img.size}")
            
            return True, ""
            
    except Exception as e:
        return False, f"Invalid or corrupted image file: {str(e)}"

def save_image(file) -> Path:
    """
    Save uploaded image with timestamp-based unique name
    Returns path to saved image
    """
    # Validate file
    is_valid, error_message = validate_image(file)
    if not is_valid:
        logger.error(f"Image validation failed: {error_message}")
        raise ValueError(error_message)
    
    # Create safe filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_filename = secure_filename(file.filename)
    filename = f"{timestamp}_{original_filename}"
    
    # Ensure upload directory exists
    image_path = Config.UPLOAD_FOLDER / filename
    image_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Convert image if necessary and save
        with Image.open(file) as img:
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            img.save(str(image_path), quality=95, optimize=True)
        
        logger.info(f"Saved image to {image_path}")
        
        # Clean up old images
        cleanup_old_images(Config.KEEP_IMAGES)
        
        return image_path
        
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        if image_path.exists():
            try:
                image_path.unlink()  # Clean up failed save
            except:
                pass
        raise ValueError(f"Failed to save image: {str(e)}")

def cleanup_old_images(keep_last: int = None):
    """Remove old images, keeping only the specified number of most recent ones"""
    if keep_last is None:
        keep_last = Config.KEEP_IMAGES
        
    try:
        images = sorted(
            [f for f in Config.UPLOAD_FOLDER.glob('*') if f.suffix.lower() in Config.SUPPORTED_FORMATS],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Remove all but the most recent files
        for image_path in images[keep_last:]:
            try:
                image_path.unlink()
                logger.info(f"Cleaned up old image: {image_path}")
            except Exception as e:
                logger.error(f"Failed to delete {image_path}: {e}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")