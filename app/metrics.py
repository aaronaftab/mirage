import logging
import time
import threading
from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from app.controller import Controller
import sys

logger = logging.getLogger(__name__)

# Display health metrics
DISPLAY_CONNECTED = Gauge(
    'mirage_display_connected',
    'Whether the e-ink display is connected and responding (1=yes, 0=no)',
    registry=REGISTRY
)

DISPLAY_LAST_UPDATE_TIMESTAMP = Gauge(
    'mirage_display_last_update_timestamp_seconds',
    'Unix timestamp of last successful display update',
    registry=REGISTRY
)

DISPLAY_CONSECUTIVE_FAILURES = Counter(
    'mirage_display_consecutive_failures',
    'Number of consecutive display update failures',
    registry=REGISTRY
)

# Display update metrics
DISPLAY_UPDATES_TOTAL = Counter(
    'mirage_display_updates_total',
    'Total number of display update attempts',
    ['status'],  # success/failure
    registry=REGISTRY
)

DISPLAY_UPDATE_DURATION = Histogram(
    'mirage_display_update_duration_seconds',
    'Time spent updating the display',
    buckets=[1, 2, 5, 10, 30],  # e-ink updates are slow
    registry=REGISTRY
)

# System metrics
SYSTEM_CPU_PERCENT = Gauge(
    'mirage_system_cpu_percent',
    'Current CPU utilization percentage',
    registry=REGISTRY
)

SYSTEM_MEMORY_PERCENT = Gauge(
    'mirage_system_memory_percent',
    'Current memory utilization percentage',
    registry=REGISTRY
)

SYSTEM_DISK_PERCENT = Gauge(
    'mirage_system_disk_percent',
    'Current disk utilization percentage',
    registry=REGISTRY
)

SYSTEM_TEMPERATURE = Gauge(
    'mirage_system_temperature_celsius',
    'Current CPU temperature in Celsius',
    registry=REGISTRY
)

# Storage metrics
IMAGE_COUNT = Gauge(
    'mirage_stored_images_total',
    'Number of images currently stored',
    registry=REGISTRY
)

IMAGE_STORAGE_BYTES = Gauge(
    'mirage_image_storage_bytes',
    'Total bytes used by stored images',
    registry=REGISTRY
)

class MetricsCollector:
    """Collects and updates system metrics"""
    
    # Class variable to track instances
    _instances = set()
    
    def __init__(self, controller: Controller, interval: int = 300):
        self.controller = controller
        self.interval = interval
        self.stop_event = threading.Event()
        
        # Start collection thread
        self.collection_thread = threading.Thread(
            target=self._collect_metrics_periodically,
            daemon=True,
            name="MetricsThread"
        )
        self.collection_thread.start()
        logger.info(f"Started metrics collection thread (interval: {interval}s)")
        
        # Track this instance
        MetricsCollector._instances.add(self)
    
    def __del__(self):
        """Cleanup when instance is garbage collected"""
        MetricsCollector._instances.discard(self)
    
    @classmethod
    def shutdown_all(cls):
        """Shutdown all collector instances"""
        if cls._instances:
            print("Shutting down all metrics collectors...")
            for collector in list(cls._instances):
                collector.shutdown()
            cls._instances.clear()
            print("All metrics collectors shutdown complete")
    
    def _collect_metrics_periodically(self):
        """Periodically collect and update metrics"""
        while not self.stop_event.is_set():
            try:
                self._update_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            # Wait for next collection or stop
            self.stop_event.wait(timeout=self.interval)
    
    def _update_metrics(self):
        """Update all metrics"""
        # Get current status
        status = self.controller.get_status()
        
        # Update system metrics
        system = status["system"]
        if temp := system["temperature"]:
            SYSTEM_TEMPERATURE.set(temp)
        
        if "cpu" in system:
            SYSTEM_CPU_PERCENT.set(system["cpu"]["percent"])
        
        if "memory" in system:
            SYSTEM_MEMORY_PERCENT.set(system["memory"]["percent"])
        
        if "disk" in system:
            SYSTEM_DISK_PERCENT.set(system["disk"]["percent"])
        
        # Update storage metrics
        storage = status["storage"]
        IMAGE_COUNT.set(storage["image_count"])
        IMAGE_STORAGE_BYTES.set(storage["total_size"])
        
        # Update display metrics
        display = status["display"]
        DISPLAY_CONSECUTIVE_FAILURES.inc(display["consecutive_failures"])
        if last_update := display["last_successful_update"]:
            DISPLAY_LAST_UPDATE_TIMESTAMP.set(last_update)
    
    def shutdown(self):
        """Shutdown this collector instance."""
        if self.collection_thread and self.collection_thread.is_alive():
            self.stop_event.set()
            try:
                self.collection_thread.join(timeout=5)
                if not self.collection_thread.is_alive():
                    print("Metrics collector thread joined successfully")
                else:
                    print("Warning: Metrics collector thread did not shut down cleanly")
            except Exception as e:
                print(f"Error during metrics shutdown: {str(e)}", file=sys.stderr)
            finally:
                MetricsCollector._instances.discard(self) 