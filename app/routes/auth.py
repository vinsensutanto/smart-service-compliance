from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from app.models.workstation import Workstation

auth_api_bp = Blueprint("auth_api", __name__)

@auth_api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    workstation_code = data.get("workstation_code")

    if not all([username, password, workstation_code]):
        return jsonify({"error": "Missing fields"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    workstation = Workstation.query.filter_by(code=workstation_code).first()
    if not workstation:
        return jsonify({"error": "Invalid workstation"}), 400

    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.name,
        "workstation": {
            "id": workstation.id,
            "code": workstation.code
        }
    })
