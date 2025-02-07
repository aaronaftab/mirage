from pathlib import Path
import logging
import time
import threading
from PIL import Image
from inky.auto import auto
from config import Config
from app.metrics import (
    DISPLAY_UPDATES_TOTAL, DISPLAY_UPDATE_DURATION,
    DISPLAY_CONNECTED, DISPLAY_LAST_UPDATE_TIMESTAMP,
    DISPLAY_CONSECUTIVE_FAILURES
)

logger = logging.getLogger(__name__)

class Display:
    # E-ink operations can be slow, especially for large images
    STATUS_TIMEOUT = 30  # 30 seconds for status check
    UPDATE_TIMEOUT = 120  # 2 minutes for display update
    
    def __init__(self):
        logger.info("Initializing display")
        self._consecutive_failures = 0
        self._last_successful_update = None
        self._lock = threading.Lock()  # Prevent concurrent hardware access
        
        try:
            self.inky = auto(verbose=True)
            logger.info(f"Display initialized with resolution {self.inky.resolution}")
            DISPLAY_CONNECTED.set(1)
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            DISPLAY_CONNECTED.set(0)
            raise
    
    def check_status(self) -> dict:
        """
        Get display status including hardware info and health.
        Tests connection by attempting to read display properties.
        """
        if not self._lock.acquire(timeout=Config.DISPLAY_STATUS_TIMEOUT):
            logger.error(f"Timeout ({Config.DISPLAY_STATUS_TIMEOUT}s) waiting for display lock during status check")
            return {
                "resolution": None,
                "colour": None,
                "supported_formats": Config.SUPPORTED_FORMATS,
                "connected": False,
                "consecutive_failures": self._consecutive_failures,
                "last_successful_update": self._last_successful_update,
                "last_error": "Display busy/locked"
            }
            
        try:
            # Test connection by reading resolution (requires device communication)
            _ = self.inky.resolution
            is_connected = True
            DISPLAY_CONNECTED.set(1)
            last_error = None
        except Exception as e:
            logger.error(f"Display connection check failed: {e}")
            is_connected = False
            DISPLAY_CONNECTED.set(0)
            last_error = str(e)
        finally:
            self._lock.release()
        
        return {
            # Hardware info (constant)
            "resolution": self.inky.resolution if is_connected else None,
            "colour": self.inky.colour if is_connected else None,
            "supported_formats": Config.SUPPORTED_FORMATS,
            
            # Health status (dynamic)
            "connected": is_connected,
            "consecutive_failures": self._consecutive_failures,
            "last_successful_update": self._last_successful_update,
            "last_error": last_error
        }
    
    def update(self, image_path: Path) -> bool:
        """Update display with new image"""
        start_time = time.time()
        
        if not self._lock.acquire(timeout=Config.DISPLAY_UPDATE_TIMEOUT):
            logger.error(f"Timeout ({Config.DISPLAY_UPDATE_TIMEOUT}s) waiting for display lock during update")
            DISPLAY_UPDATES_TOTAL.labels(status="failure").inc()
            self._consecutive_failures += 1
            DISPLAY_CONSECUTIVE_FAILURES.inc()
            return False
            
        try:
            if image_path.suffix.lower() not in Config.SUPPORTED_FORMATS:
                logger.error(f"Unsupported format {image_path.suffix}. Supported formats: {Config.SUPPORTED_FORMATS}")
                DISPLAY_UPDATES_TOTAL.labels(status="failure").inc()
                self._consecutive_failures += 1
                DISPLAY_CONSECUTIVE_FAILURES.inc()
                return False
            
            logger.info(f"Updating display with image: {image_path}")
            
            # Break down the update into steps for better logging
            try:
                with Image.open(image_path) as image:
                    logger.debug("Image opened successfully")
                    resized = image.resize(self.inky.resolution)
                    logger.debug("Image resized successfully")
                    self.inky.set_image(resized)
                    logger.debug("Image set to display buffer")
                    logger.info(f"Starting display refresh (this may take up to {Config.DISPLAY_UPDATE_TIMEOUT}s)...")
                    self.inky.show()
                    logger.debug("Display refresh completed")
            except Exception as e:
                logger.error(f"Display hardware operation failed: {e}", exc_info=True)
                raise
            
            duration = time.time() - start_time
            DISPLAY_UPDATE_DURATION.observe(duration)
            DISPLAY_UPDATES_TOTAL.labels(status="success").inc()
            
            # Update success metrics
            self._consecutive_failures = 0
            self._last_successful_update = time.time()
            DISPLAY_LAST_UPDATE_TIMESTAMP.set(self._last_successful_update)
            
            logger.info(f"Display update successful (took {duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            DISPLAY_UPDATE_DURATION.observe(duration)
            DISPLAY_UPDATES_TOTAL.labels(status="failure").inc()
            
            # Update failure metrics
            self._consecutive_failures += 1
            DISPLAY_CONSECUTIVE_FAILURES.inc()
            
            logger.error(f"Display update failed: {e}", exc_info=True)
            return False
            
        finally:
            self._lock.release()
