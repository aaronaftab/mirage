# app/system_monitor.py
import psutil
from datetime import datetime
from pathlib import Path

class SystemMonitor:
    def __init__(self):
        self.image_dir = Path('instance/images')

    def get_cpu_temperature(self) -> float:
        """Get CPU temperature using system file"""
        try:
            temp = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
            return float(temp) / 1000.0
        except:
            try:
                temp = os.popen('vcgencmd measure_temp').readline()
                return float(temp.replace('temp=', '').replace('\'C\n', ''))
            except:
                return None

    def get_system_stats(self) -> dict:
        """Get comprehensive system statistics"""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(),
                "count": psutil.cpu_count(),
                "temperature": self.get_cpu_temperature(),
                "frequency": psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "swap_percent": psutil.swap_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": {
                "interfaces": psutil.net_if_addrs(),
                "connections": len(psutil.net_connections())
            },
            "uptime": int(datetime.now().timestamp() - psutil.boot_time()),
            "timestamp": datetime.now().isoformat()
        }

    def get_storage_stats(self) -> dict:
        """Get image storage statistics"""
        images = list(self.image_dir.glob('*.*'))
        return {
            "total_images": len(images),
            "total_size": sum(f.stat().st_size for f in images),
            "recent_images": [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
                }
                for f in sorted(images, key=lambda x: x.stat().st_ctime, reverse=True)[:5]
            ]
        }

    def get_status(self) -> dict:
        """Get complete system status"""
        return {
            "system": self.get_system_stats(),
            "storage": self.get_storage_stats()
        }
