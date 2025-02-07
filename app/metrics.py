from prometheus_client import Counter, Gauge, Histogram, REGISTRY
import time

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