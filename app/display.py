from pathlib import Path
from PIL import Image
from inky.auto import auto

class Display:
    def __init__(self):
        self.inky = auto(verbose=True)
        self.supported_formats = ['.png', '.jpg', '.jpeg']
    
    def get_status(self) -> dict:
        """Return current display status"""
        return {
            "resolution": self.inky.resolution,
            "colour": self.inky.colour,
            "supported_formats": self.supported_formats
        }
        
    def update(self, image_path: Path) -> bool:
        """Update display with new image"""
        try:
            if image_path.suffix.lower() not in self.supported_formats:
                print(f"Error: Unsupported format. Use: {self.supported_formats}")
                return False
            
            with Image.open(image_path) as image:
                resized = image.resize(self.inky.resolution)
                self.inky.set_image(resized)
                self.inky.show()
            return True
            
        except Exception as e:
            print(f"Display update failed: {e}")
            return False
