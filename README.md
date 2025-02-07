# Mirage - E-Ink Display Controller

A Flask-based web service for controlling an e-ink display on a Raspberry Pi. Features include image display, system monitoring, and hardware control.

## Features

- 🖼️ E-ink display control with image upload and validation
- 📊 System monitoring (CPU, memory, temperature, disk usage)
- 🔄 Service control (start/stop/restart)
- ⚡ Power management (reboot/shutdown)
- 📈 Prometheus metrics endpoint
- 🔒 Optional API authentication
- 📝 Comprehensive logging

## Requirements

- Raspberry Pi (tested on Pi 4)
- Compatible e-ink display (using Pimoroni Inky library)
- Python 3.11+
- virtualenv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mirage
```

2. Create and activate a virtual environment:
```bash
python -m venv ~/.virtualenvs/pimoroni
source ~/.virtualenvs/pimoroni/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
# Optional: Set environment variables
export LOG_LEVEL=INFO
export METRICS_INTERVAL=300  # 5 minutes
export KEEP_IMAGES=5  # Number of images to retain
export API_TOKEN=your-secret-token  # For API authentication
```

## Running the Application

1. Start the application using Gunicorn:
```bash
gunicorn -b 0.0.0.0:5000 wsgi:app
```

2. For development/testing:
```bash
PYTHONPATH=. FLASK_APP=app FLASK_ENV=development flask run
```

## API Endpoints

### Display Control
- `POST /display` - Upload and display an image
  - Accepts multipart/form-data with 'image' field
  - Supports JPG and PNG formats
  - Max file size: 5MB

### System Status
- `GET /status` - Get comprehensive system status
- `GET /metrics` - Prometheus metrics endpoint
- `GET /system/temperature` - Get CPU temperature
- `GET /system/service/status` - Get service status

### System Control
- `POST /system/service/<action>` - Control service (start/stop/restart)
- `POST /system/power/<action>` - Control system power (reboot/shutdown)

## Testing

Run the test suite:
```bash
source ~/.virtualenvs/pimoroni/bin/activate
PYTHONPATH=. pytest app/tests -v
```

## Configuration

Key configuration options in `config.py`:

```python
# File upload settings
UPLOAD_FOLDER = Path('instance/images')
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
KEEP_IMAGES = 5  # Number of images to retain

# Display settings
SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg']
METRICS_INTERVAL = 300  # 5 minutes
DISPLAY_STATUS_TIMEOUT = 30  # seconds
DISPLAY_UPDATE_TIMEOUT = 120  # seconds

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
LOG_FILE = Path('logs/mirage.log')
```

## Systemd Service

1. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/mirage.service
```

2. Add the following content:
```ini
[Unit]
Description=Mirage E-Ink Display Controller
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/mirage
Environment="PATH=/home/pi/.virtualenvs/pimoroni/bin"
ExecStart=/home/pi/.virtualenvs/pimoroni/bin/gunicorn -b 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable mirage
sudo systemctl start mirage
```

## Monitoring

The application exposes Prometheus metrics at `/metrics` including:
- Display connection status
- Display update success/failure counts
- System resource utilization
- Image storage statistics

## Development

### Project Structure
```
mirage/
├── app/
│   ├── hardware/         # Hardware interfaces
│   ├── tests/           # Test suite
│   ├── __init__.py      # Application factory
│   ├── controller.py    # Main controller
│   ├── metrics.py       # Prometheus metrics
│   ├── routes.py        # API endpoints
│   └── utils.py         # Utility functions
├── config.py            # Configuration
├── requirements.txt     # Dependencies
└── wsgi.py             # WSGI entry point
```

### Adding New Features

1. Hardware support:
   - Add new hardware interfaces in `app/hardware/`
   - Update `Controller` class to integrate new hardware
   - Add corresponding metrics in `metrics.py`

2. API endpoints:
   - Add routes in `routes.py`
   - Update tests in `tests/unit/`
   - Document new endpoints

## Troubleshooting

1. Display issues:
   - Check display connection status via `/status`
   - Review logs in `logs/mirage.log`
   - Verify display permissions

2. Service issues:
   - Check service status: `systemctl status mirage`
   - Review journal logs: `journalctl -u mirage`

3. Permission issues:
   - Ensure proper file permissions for logs and uploads
   - Verify GPIO access permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[MIT License](LICENSE) 