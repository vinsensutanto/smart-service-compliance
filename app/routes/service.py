from flask import Blueprint, request, jsonify
from flask_login import current_user

service_bp = Blueprint("service", __name__)

@service_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "ok",
        "message": "service routes alive"
    })

@service_bp.route("/debug-user", methods=["GET"])
def debug_user():
    return {
        "is_authenticated": current_user.is_authenticated,
        "user_id": getattr(current_user, "user_id", None),
        "role_id": getattr(current_user, "role_id", None)
    }
