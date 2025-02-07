import pytest
from flask import url_for
import json
from werkzeug.datastructures import FileStorage

def test_metrics_endpoint(client):
    """Test the Prometheus metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'text/plain; version=0.0.4' in response.content_type
    assert 'charset=utf-8' in response.content_type
    
def test_status_endpoint(client):
    """Test the status endpoint"""
    response = client.get('/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check required fields
    assert 'status' in data
    assert data['status'] == 'online'
    assert 'display' in data
    assert 'system' in data
    assert 'storage' in data
    
    # Check display info
    display = data['display']
    assert 'resolution' in display
    assert 'colour' in display
    assert 'connected' in display
    assert 'supported_formats' in display
    
    # Check system info
    system = data['system']
    assert 'cpu' in system
    assert 'memory' in system
    assert 'disk' in system

def test_display_endpoint_no_file(client):
    """Test display endpoint with no file"""
    response = client.post('/display')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No image file provided' in data['error']

def test_display_endpoint_empty_filename(client, test_image):
    """Test display endpoint with empty filename"""
    data = {
        'image': (test_image, '')
    }
    response = client.post('/display', data=data)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'No selected file' in data['error']

def test_display_endpoint_invalid_file(client, corrupt_image):
    """Test display endpoint with invalid file"""
    data = {
        'image': (corrupt_image, 'test.png')
    }
    response = client.post('/display', data=data)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid or corrupted image file' in data['error']

def test_display_endpoint_success(client, test_image):
    """Test successful display update"""
    data = {
        'image': (test_image, 'test.png')
    }
    response = client.post('/display', data=data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Display updated successfully' in data['message']

def test_system_service_status(client, monkeypatch):
    """Test service status endpoint"""
    # Mock the service status to return a known state
    def mock_get_service_status(self):
        return {
            "active": True,
            "state": "active (running)",
            "details": "Service is running normally"
        }
    
    monkeypatch.setattr("app.hardware.system.SystemHardware.get_service_status", mock_get_service_status)
    
    response = client.get('/system/service/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert "active" in data
    assert data["active"] is True
    assert "state" in data
    assert "active (running)" in data["state"]
    assert "details" in data

@pytest.mark.parametrize('action', ['start', 'stop', 'restart'])
def test_system_service_control(client, action, monkeypatch):
    """Test service control endpoint"""
    # Mock the control_service method to prevent actual service commands
    def mock_control_service(self, cmd):
        if cmd not in ['start', 'stop', 'restart']:
            raise ValueError("Invalid action")
        return True, f"Service {cmd} successful"
    
    monkeypatch.setattr("app.hardware.system.SystemHardware.control_service", mock_control_service)
    
    # Test valid action
    response = client.post(f'/system/service/{action}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "message" in data
    assert f"Service {action} successful" in data["message"]
    
    # Test invalid action
    response = client.post('/system/service/invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data

@pytest.mark.parametrize('action', ['reboot', 'shutdown'])
def test_system_power_control(client, action, monkeypatch):
    """Test power control endpoint"""
    # Mock the control_power method to prevent actual system commands
    def mock_control_power(self, cmd):
        if cmd not in ['reboot', 'shutdown']:
            raise ValueError("Invalid action")
        return True, f"System {cmd} initiated"
    
    monkeypatch.setattr("app.hardware.system.SystemHardware.control_power", mock_control_power)
    
    # Test valid action
    response = client.post(f'/system/power/{action}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "message" in data
    assert f"System {action} initiated" in data["message"]
    
    # Test invalid action
    response = client.post('/system/power/invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data

def test_system_temperature(client):
    """Test temperature endpoint"""
    response = client.get('/system/temperature')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "temperature" in data
    # Temperature should be a reasonable value for a Raspberry Pi
    assert isinstance(data["temperature"], (int, float))
    assert 0 <= data["temperature"] <= 100  # Reasonable range in Celsius 