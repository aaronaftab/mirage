import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from app.hardware.system import SystemHardware
from app.controller import Controller

@pytest.fixture
def mock_display():
    display = Mock()
    display.get_info.return_value = {
        "resolution": [800, 480],
        "colour": "multi",
        "connected": True,
        "supported_formats": [".jpg", ".png"],
        "consecutive_failures": 0,
        "last_successful_update": None
    }
    return display

@pytest.fixture
def mock_system():
    system = Mock()
    system.get_temperature.return_value = 45.6
    system.get_service_status.return_value = {
        "active": True,
        "state": "active (running)",
        "details": "Service is running"
    }
    system.get_system_stats.return_value = {
        "cpu": {
            "percent": 25.0,
            "count": 4,
            "temperature": 45.6,
            "frequency": 1400.0
        },
        "memory": {
            "total": 8589934592,
            "available": 4294967296,
            "percent": 50.0,
            "swap_percent": 10.0
        },
        "disk": {
            "total": 64424509440,
            "free": 32212254720,
            "percent": 50.0
        }
    }
    return system

def test_system_hardware_temperature_sysfs():
    """Test reading temperature from sysfs"""
    with patch('pathlib.Path.read_text') as mock_read:
        mock_read.return_value = "45600"  # 45.6°C
        system = SystemHardware()
        temp = system.get_temperature()
        assert temp == 45.6
        mock_read.assert_called_once()

def test_system_hardware_temperature_vcgencmd():
    """Test reading temperature from vcgencmd"""
    with patch('pathlib.Path.read_text') as mock_read:
        mock_read.side_effect = FileNotFoundError()
        
        with patch.object(SystemHardware, 'run_command') as mock_run:
            mock_run.return_value = (True, "temp=45.6'C")
            system = SystemHardware()
            temp = system.get_temperature()
            assert temp == 45.6
            mock_run.assert_called_once_with(['vcgencmd', 'measure_temp'])

def test_system_hardware_service_control():
    """Test service control commands"""
    system = SystemHardware()
    
    with patch.object(SystemHardware, 'run_command') as mock_run:
        mock_run.return_value = (True, "Service started")
        
        # Test valid actions
        success, _ = system.control_service('start')
        assert success
        mock_run.assert_called_with(['sudo', 'systemctl', 'start', 'mirage'])
        
        # Test invalid action
        with pytest.raises(ValueError):
            system.control_service('invalid')

def test_system_hardware_power_control():
    """Test power control commands"""
    system = SystemHardware()
    
    with patch.object(SystemHardware, 'run_command') as mock_run:
        mock_run.return_value = (True, "Shutdown initiated")
        
        # Test valid actions
        success, _ = system.control_power('shutdown')
        assert success
        mock_run.assert_called_with(['sudo', 'shutdown', '-h', 'now'])
        
        # Test invalid action
        with pytest.raises(ValueError):
            system.control_power('invalid')

def test_controller_status(mock_display, mock_system):
    """Test controller status aggregation"""
    controller = Controller(mock_display, mock_system)
    status = controller.get_status()
    
    assert status["status"] == "online"
    assert "display" in status
    assert "system" in status
    assert "storage" in status
    
    # Check system info
    system = status["system"]
    assert system["temperature"] == 45.6
    assert system["cpu"]["percent"] == 25.0
    assert system["memory"]["percent"] == 50.0
    
    # Check display info
    display = status["display"]
    assert display["resolution"] == [800, 480]
    assert display["connected"] is True

def test_controller_storage_stats(mock_display, mock_system, tmp_path):
    """Test storage statistics collection"""
    # Create some test files
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "test1.jpg").write_bytes(b"test1")
    (image_dir / "test2.png").write_bytes(b"test2")
    (image_dir / "test3.txt").write_bytes(b"test3")  # Should be ignored
    
    controller = Controller(mock_display, mock_system)
    controller.image_dir = image_dir
    
    stats = controller.get_storage_stats()
    assert stats["image_count"] == 2  # Only jpg and png
    assert stats["total_size"] == 10  # 5 bytes each

def test_controller_display_update(mock_display, mock_system):
    """Test display update handling"""
    mock_display.update.return_value = True
    controller = Controller(mock_display, mock_system)
    
    # Mock the save_image function
    with patch('app.controller.save_image') as mock_save:
        mock_save.return_value = Path("/tmp/test.jpg")
        
        # Test successful update
        success, error = controller.update_display(Mock())
        assert success
        assert error is None
        
        # Test failed update
        mock_display.update.return_value = False
        success, error = controller.update_display(Mock())
        assert not success
        assert error == "Display update failed" 