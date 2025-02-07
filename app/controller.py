import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from app.hardware.display import Display
from app.hardware.system import SystemHardware
from app.utils import save_image
from config import Config

logger = logging.getLogger(__name__)

class Controller:
    """High-level system controller for display and hardware management"""
    
    def __init__(self, display: Display, system: SystemHardware):
        self.display = display
        self.system = system
        self.image_dir = Config.UPLOAD_FOLDER
    
    def get_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "status": "online",
            "system": {
                "temperature": self.system.get_temperature(),
                "service": self.system.get_service_status(),
                **self.system.get_system_stats()
            },
            "storage": self.get_storage_stats(),
            "display": self.display.get_info()
        }
    
    def get_storage_stats(self) -> Dict:
        """Get image storage statistics"""
        try:
            if not self.image_dir.exists():
                return {"image_count": 0, "total_size": 0}
            
            total_size = 0
            image_count = 0
            
            for file in self.image_dir.glob('*'):
                if file.suffix.lower() in Config.SUPPORTED_FORMATS:
                    total_size += file.stat().st_size
                    image_count += 1
            
            logger.debug(f"Storage stats: {image_count} images, {total_size} bytes")
            return {
                "image_count": image_count,
                "total_size": total_size
            }
        except Exception as e:
            logger.error(f"Failed to collect storage stats: {e}", exc_info=True)
            return {"image_count": 0, "total_size": 0}
    
    def update_display(self, image_file) -> Tuple[bool, Optional[str]]:
        """Process and update display with new image"""
        try:
            image_path = save_image(image_file)
            success = self.display.update(str(image_path))
            return success, None if success else "Display update failed"
        except Exception as e:
            logger.error(f"Display update failed: {e}", exc_info=True)
            return False, str(e)
    
    def control_service(self, action: str) -> Tuple[bool, str]:
        """Control the system service"""
        return self.system.control_service(action)
    
    def control_power(self, action: str) -> Tuple[bool, str]:
        """Control system power"""
        return self.system.control_power(action) 