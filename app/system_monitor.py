# app/system_monitor.py
import psutil
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from config import Config
from app.metrics import (
    SYSTEM_CPU_PERCENT, SYSTEM_MEMORY_PERCENT, SYSTEM_DISK_PERCENT,
    SYSTEM_TEMPERATURE, IMAGE_COUNT, IMAGE_STORAGE_BYTES
)

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, *, display, metrics_interval=None):
        """
        Initialize SystemMonitor
        
        Args:
            display: Display instance to monitor
            metrics_interval: Optional override for metrics collection interval
        """
        self.display = display
        self.image_dir = Config.UPLOAD_FOLDER
        self.metrics_interval = metrics_interval or Config.METRICS_INTERVAL
        logger.info(f"SystemMonitor initialized with {self.metrics_interval}s metrics interval")
        
        # Use an event for cleaner thread signaling
        self.stop_event = threading.Event()
        
        # Start background metrics update thread
        self.update_thread = threading.Thread(
            target=self._update_metrics_periodically,
            daemon=True,
            name="MetricsThread"
        )
        self.update_thread.start()
        logger.info("Started background metrics update thread")

    def _update_metrics_periodically(self):
        """Background thread to update metrics periodically"""
        while not self.stop_event.is_set():
            start_time = time.time()
            try:
                # Collect metrics with timeouts
                self._safe_collect_metrics()
                
                # Calculate sleep time to maintain consistent interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.metrics_interval - elapsed)
                
                # Use event to allow for clean shutdown
                self.stop_event.wait(timeout=sleep_time)
                
            except Exception as e:
                logger.error(f"Error in metrics update thread: {e}", exc_info=True)
                # Still honor the interval on error
                self.stop_event.wait(timeout=self.metrics_interval)

    def _safe_collect_metrics(self):
        """Collect metrics with timeouts to prevent hanging"""
        try:
            # System stats are usually fast
            self.get_system_stats()
        except Exception as e:
            logger.error(f"Failed to collect system stats: {e}")

        try:
            # File operations could be slow
            self.get_storage_stats()
        except Exception as e:
            logger.error(f"Failed to collect storage stats: {e}")

        try:
            # Hardware communication could hang
            self.display.check_status()
        except Exception as e:
            logger.error(f"Failed to check display status: {e}")

    def shutdown(self):
        """Gracefully shutdown the background thread"""
        logger.info("Shutting down SystemMonitor")
        self.stop_event.set()
        
        # Give thread time to cleanup
        self.update_thread.join(timeout=10)
        
        if self.update_thread.is_alive():
            logger.warning("Metrics thread did not shut down cleanly")
        else:
            logger.info("Metrics thread shut down successfully")

    def get_cpu_temperature(self) -> float:
        """Get CPU temperature using system file"""
        try:
            temp = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
            temp_value = float(temp) / 1000.0
            SYSTEM_TEMPERATURE.set(temp_value)
            return temp_value
        except Exception as e:
            try:
                temp = os.popen('vcgencmd measure_temp').readline()
                temp_value = float(temp.replace('temp=', '').replace('\'C\n', ''))
                SYSTEM_TEMPERATURE.set(temp_value)
                return temp_value
            except Exception as e2:
                logger.error(f"Failed to read CPU temperature: {e2}")
                return None

    def get_system_stats(self) -> dict:
        """Get comprehensive system statistics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update Prometheus metrics
            SYSTEM_CPU_PERCENT.set(cpu_percent)
            SYSTEM_MEMORY_PERCENT.set(memory.percent)
            SYSTEM_DISK_PERCENT.set(disk.percent)
            
            stats = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "temperature": self.get_cpu_temperature(),
                    "frequency": psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "swap_percent": psutil.swap_memory().percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
            
            logger.debug(f"System stats collected: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to collect system stats: {e}", exc_info=True)
            return {}

    def get_storage_stats(self) -> dict:
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
            
            # Update Prometheus metrics
            IMAGE_COUNT.set(image_count)
            IMAGE_STORAGE_BYTES.set(total_size)
            
            logger.debug(f"Storage stats: {image_count} images, {total_size} bytes")
            return {
                "image_count": image_count,
                "total_size": total_size
            }
        except Exception as e:
            logger.error(f"Failed to collect storage stats: {e}", exc_info=True)
            return {"image_count": 0, "total_size": 0}

    def get_status(self) -> dict:
        """Get complete system status"""
        return {
            "system": self.get_system_stats(),
            "storage": self.get_storage_stats()
        }
