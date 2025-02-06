from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config
import os

def save_image(file) -> Path:
    """
    Save uploaded image with timestamp-based unique name
    Returns path to saved image
    """
    # Create safe filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_filename = secure_filename(file.filename)
    filename = f"{timestamp}_{original_filename}"
    
    # Ensure upload directory exists
    image_path = Path(Config.UPLOAD_FOLDER) / filename
    image_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file.save(str(image_path))
    
    # Clean up old images (keep last 5)
    cleanup_old_images()
    
    return image_path

def cleanup_old_images(keep_last: int = 5):
    """Remove old images, keeping only the specified number of most recent ones"""
    try:
        images = sorted(Path(Config.UPLOAD_FOLDER).glob('*.*'), 
                       key=os.path.getctime, 
                       reverse=True)
        
        # Remove all but the most recent files
        for image_path in images[keep_last:]:
            image_path.unlink()
    except Exception as e:
        print(f"Cleanup error: {e}")