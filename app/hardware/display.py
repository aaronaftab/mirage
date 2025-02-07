import logging
import time
import threading
from PIL import Image
from inky.auto import auto
from config import Config

logger = logging.getLogger(__name__)

class Display:
    """Hardware interface for the e-ink display"""
    
    def __init__(self):
        """Initialize the display hardware"""
        logger.info("Initializing display")
        self._consecutive_failures = 0
        self._last_successful_update = None
        self._lock = threading.Lock()  # Prevent concurrent hardware access
        
        try:
            self.inky = auto(verbose=True)
            self.resolution = self.inky.resolution
            self.colour = self.inky.colour
            logger.info(f"Display initialized with resolution {self.resolution}")
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            raise
    
    def get_info(self) -> dict:
        """Get display hardware information"""
        return {
            "resolution": self.resolution,
            "colour": self.colour,
            "connected": True,  # We know it's connected if initialization succeeded
            "supported_formats": Config.SUPPORTED_FORMATS,
            "consecutive_failures": self._consecutive_failures,
            "last_successful_update": self._last_successful_update
        }
    
    def update(self, image_path: str) -> bool:
        """Update display with new image"""
        start_time = time.time()
        
        if not self._lock.acquire(timeout=Config.DISPLAY_UPDATE_TIMEOUT):
            logger.error(f"Timeout ({Config.DISPLAY_UPDATE_TIMEOUT}s) waiting for display lock")
            self._consecutive_failures += 1
            return False
            
        try:
            logger.info(f"Updating display with image: {image_path}")
            
            # Break down the update into steps for better logging
            with Image.open(image_path) as image:
                logger.debug("Image opened successfully")
                resized = image.resize(self.resolution)
                logger.debug("Image resized successfully")
                self.inky.set_image(resized)
                logger.debug("Image set to display buffer")
                logger.info(f"Starting display refresh (this may take up to {Config.DISPLAY_UPDATE_TIMEOUT}s)...")
                self.inky.show()
                logger.debug("Display refresh completed")
            
            # Update success metrics
            self._consecutive_failures = 0
            self._last_successful_update = time.time()
            
            duration = time.time() - start_time
            logger.info(f"Display update successful (took {duration:.2f}s)")
            return True
            
        except Exception as e:
            self._consecutive_failures += 1
            logger.error(f"Display update failed: {e}", exc_info=True)
            return False
            
        finally:
            self._lock.release() 