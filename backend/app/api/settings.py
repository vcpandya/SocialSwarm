"""
Settings API endpoints
"""

import traceback
from flask import request, jsonify

from . import settings_bp
from ..services.settings_manager import SettingsManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.settings')


@settings_bp.route('/status', methods=['GET'])
def get_settings_status():
    """Check if required configuration is present."""
    try:
        status = SettingsManager.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        logger.error(f"Failed to get settings status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('', methods=['GET'])
def get_settings():
    """Get current settings with masked API keys."""
    try:
        current = SettingsManager.get_current()
        return jsonify({"success": True, "data": current})
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@settings_bp.route('', methods=['POST'])
def save_settings():
    """Save settings (partial or full update)."""
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({"success": False, "error": "No settings provided"}), 400

        SettingsManager.merge_and_save(data)
        current = SettingsManager.get_current()
        status = SettingsManager.get_status()

        return jsonify({
            "success": True,
            "data": current,
            "status": status,
        })
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@settings_bp.route('/validate', methods=['POST'])
def validate_settings():
    """Validate a settings group by testing the connection."""
    try:
        data = request.get_json() or {}
        group = data.get('group')
        values = data.get('values', {})

        if group == 'llm':
            api_key = values.get('api_key', '')
            base_url = values.get('base_url', '')
            model_name = values.get('model_name', '')
            if not api_key or not model_name:
                return jsonify({"success": True, "valid": False, "error": "API key and model name are required"})
            valid, message = SettingsManager.validate_llm(api_key, base_url, model_name)
            return jsonify({"success": True, "valid": valid, "message": message})

        elif group == 'zep':
            api_key = values.get('api_key', '')
            if not api_key:
                return jsonify({"success": True, "valid": False, "error": "API key is required"})
            valid, message = SettingsManager.validate_zep(api_key)
            return jsonify({"success": True, "valid": valid, "message": message})

        else:
            return jsonify({"success": False, "error": f"Unknown group: {group}"}), 400

    except Exception as e:
        logger.error(f"Settings validation failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
