# app/routes.py
import logging
from flask import Blueprint, jsonify, request, Response, current_app
from app.utils import save_image
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
        status = {
            "status": "online",
            "display": current_app.display.check_status(),
            **current_app.system_monitor.get_status()
        }
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
        logger.info(f"Processing image upload: {image_file.filename}")
        image_path = save_image(image_file)
        if current_app.display.update(image_path):
            logger.info(f"Display successfully updated with {image_file.filename}")
            return jsonify({"message": "Display updated successfully"})
        logger.error("Display update failed")
        return jsonify({"error": "Failed to update display"}), 500
    except Exception as e:
        logger.error(f"Display update failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
