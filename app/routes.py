# app/routes.py
import logging
from flask import Blueprint, jsonify, request, Response, current_app
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@bp.route('/status', methods=['GET'])
def get_status():
    """Get system and display status"""
    try:
        status = current_app.controller.get_status()
        logger.info("Status request successful")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status request failed: {e}", exc_info=True)
        return jsonify({"error": "Failed to get status"}), 500

@bp.route('/display', methods=['POST'])
def update_display():
    """Update the e-ink display with a new image"""
    if 'image' not in request.files:
        logger.warning("No image file provided in request")
        return jsonify({"error": "No image file provided"}), 400
        
    image_file = request.files['image']
    if image_file.filename == '':
        logger.warning("Empty filename provided")
        return jsonify({"error": "No selected file"}), 400
        
    try:
        success, error = current_app.controller.update_display(image_file)
        if success:
            logger.info(f"Display successfully updated with {image_file.filename}")
            return jsonify({"message": "Display updated successfully"})
        logger.error(f"Display update failed: {error}")
        return jsonify({"error": error}), 500
    except Exception as e:
        logger.error(f"Display update failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@bp.route('/system/service/status')
def service_status():
    """Get Gunicorn service status"""
    try:
        status = current_app.controller.get_status()["system"]["service"]
        return jsonify(status)
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/system/service/<action>', methods=['POST'])
def service_control(action):
    """Control Gunicorn service"""
    try:
        success, output = current_app.controller.control_service(action)
        if success:
            return jsonify({"message": f"Service {action} successful"})
        else:
            return jsonify({"error": f"Service {action} failed", "details": output}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Service control failed: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/system/power/<action>', methods=['POST'])
def power_control(action):
    """Control system power"""
    try:
        success, output = current_app.controller.control_power(action)
        if success:
            return jsonify({"message": f"System {action} initiated"})
        else:
            return jsonify({"error": f"System {action} failed", "details": output}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Power control failed: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/system/temperature')
def system_temperature():
    """Get system temperature"""
    try:
        temp = current_app.controller.get_status()["system"]["temperature"]
        if temp is not None:
            return jsonify({"temperature": temp})
        return jsonify({"error": "Failed to read temperature"}), 500
    except Exception as e:
        logger.error(f"Failed to get temperature: {e}")
        return jsonify({"error": str(e)}), 500
