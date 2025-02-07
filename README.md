# Mirage - The AI Photo Frame

<div align="center">
 <video src="https://github.com/user-attachments/assets/53c1dbe3-d2bb-4ab5-85f6-6cf322f16078" width="100%"></video>
</div>

 <img src="https://github.com/user-attachments/assets/0ef98b4c-3d3a-489b-9ac7-8e9cae9dafe1" width="100%" />
 <img src="https://github.com/user-attachments/assets/1d45bc56-0f07-4998-b61e-7729b9a573b0" width="100%" />
 <img src="https://github.com/user-attachments/assets/2690e96d-5d26-4b5f-bb35-3bb84cf49356" width="100%" />

## Overview

<div align="center">
 <img src="https://github.com/user-attachments/assets/1c93ff0c-8e0e-428f-9f81-729271be6c96" width="100%">
</div>

[Mirage Frame](https://themirageframe.com/) was inspired by the above tweets (it's not quite poster size, but it's also a lot cheaper than $4000!) and created to showcase both state-of-the-art AI models and the latest e-ink display technology. The full product includes the professionally built frame/display, an iOS/Android app to control it, and integration with our web server for image generation. Modes include the following, with more to come:

- Face Remix: see yourself and your loved ones in famous paintings
- Local Remix: see your local cityscape or natural scenery illustrated in different styles
- Free Prompt: create your own AI images
- Upload: upload any image

This Github repo will show you how to make a working prototype that can be controlled by your computer but will require you to bring your own API key/images for models you want to use (and set up all the hardware/software, of course). So if you prefer to skip all that, you can [buy it here](https://themirageframe.com/). Otherwise, let's get started! 

## Prototype Features

- 🖼️ E-ink display control with image upload and validation
- 📊 System monitoring (CPU, memory, temperature, disk usage)
- 🔄 Service control (start/stop/restart)
- ⚡ Power management (reboot/shutdown)
- 📈 Prometheus metrics endpoint
- 🔒 Optional API authentication
- 📝 Comprehensive logging

## Hardware Requirements

- Raspberry Pi Zero 2 W (works with any Pi version that has a 40 pin header)
- [Inky Impressions 7.3" E-Ink Display](https://shop.pimoroni.com/products/inky-impression-7-3?variant=40512683376723)
- SD card (32GB+ recommended) for Pi
- Power source compatible with your Pi model
- Enclosure (frame) materials; the prototype in the video uses [this shadow box from Amazon](https://www.amazon.com/dp/B096HCNND1), spacers made from cardboard, mounting tape, and a paper border cut out from an old picture frame

## Hardware Setup

If you haven't already, install Raspberry Pi OS Lite 64-bit (or the appropriate OS for your Pi) using [these instructions](https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system). Set up WiFi and SSH and make sure you enable SPI and I2C interfaces in system settings.

The screen is a hat for the Pi, so you can simply plug it in. Mount the screen + Pi inside your enclosure as you desire (you can see our hacky example below), connect the power source, and SSH into your Pi.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mirage
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
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
source venv/bin/activate
PYTHONPATH=. pytest app/tests -v
```

Your display should look like this:

<div align="center">
 <img src="https://github.com/user-attachments/assets/0e981bee-5e86-4708-9f8a-0d3523e93fac" width="100%">
</div>

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

1. Copy the service file to systemd:
```bash
sudo cp systemd/mirage.service /etc/systemd/system/
```

2. Enable and start the service:
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
