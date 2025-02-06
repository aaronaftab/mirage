# app/routes.py
from flask import Blueprint, jsonify, request
from app import display, system_monitor

bp = Blueprint('main', __name__)

@bp.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "online",
        "display": display.get_status(),
        **system_monitor.get_status()
    })

@bp.route('/display', methods=['POST'])
def update_display():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
        
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        image_path = save_image(image_file)
        if display.update(image_path):
            return jsonify({"message": "Display updated successfully"})
        return jsonify({"error": "Failed to update display"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
