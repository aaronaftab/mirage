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