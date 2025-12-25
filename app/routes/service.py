# app/routes/service.py
from flask import Blueprint, request, jsonify, render_template
import tempfile
import os

from app.services.service_detector import detect_service
from app.services.sop_engine import load_sop_by_service_id
from app.models.service_checklist import ServiceChecklist
from app.services.whisper_model import get_whisper_model

service_bp = Blueprint("service", __name__)


# =====================================================
# DEBUG: Audio → Transcript → Service → SOP
# =====================================================
@service_bp.route("/debug-audio-sop", methods=["POST"])
def debug_audio_sop():
    if "audio" not in request.files:
        return jsonify({"error": "audio file required"}), 400

    audio = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio.save(tmp.name)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()
        result = model.transcribe(tmp_path, language="id", verbose=False)
        transcript = result.get("text", "").strip()
    finally:
        os.remove(tmp_path)

    if not transcript:
        return jsonify({
            "transcript": "",
            "service_detected": None,
            "confidence": 0,
            "sop": None
        })

    service_id, service_name, confidence, keywords = detect_service(transcript)

    if not service_id:
        return jsonify({
            "transcript": transcript,
            "service_detected": None,
            "confidence": 0,
            "matched_keywords": [],
            "sop": None
        })

    sop = load_sop_by_service_id(service_id)

    return jsonify({
        "transcript": transcript,
        "service_id": service_id,
        "service_name": service_name,
        "confidence": confidence,
        "matched_keywords": keywords,
        "sop": sop
    })


# =====================================================
# JSON API: Checklist items per ServiceRecord
# =====================================================
@service_bp.route("/checklist/<service_record_id>")
def get_checklist(service_record_id):
    items = ServiceChecklist.query.filter_by(
        service_record_id=service_record_id
    ).all()

    return jsonify([item.to_dict() for item in items])


# =====================================================
# HTML Page: Checklist Viewer
# =====================================================
@service_bp.route("/page/checklist/<service_record_id>")
def checklist_page(service_record_id):
    return render_template(
        "checklist.html",
        service_record_id=service_record_id
    )
