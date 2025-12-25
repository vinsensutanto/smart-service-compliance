from flask import Blueprint, jsonify
from app.extensions import db
from app.models.service_record import ServiceRecord
from app.services.sop_engine import load_sop_by_service_id

sop_bp = Blueprint("sop", __name__)


@sop_bp.route("/sop/<service_record_id>")
def show_sop(service_record_id):
    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first_or_404()
    )

    if not record.service_id:
        return jsonify({
            "message": "Service not detected yet"
        }), 400

    sop = load_sop_by_service_id(record.service_id)

    if not sop:
        return jsonify({
            "message": "SOP not found for detected service",
            "service_id": record.service_id
        }), 404

    return jsonify({
        "service_record_id": record.service_record_id,
        "service": record.service_detected,
        "confidence": record.confidence,
        "sop": sop
    })
