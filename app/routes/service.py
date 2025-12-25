# app/routes/service.py
from flask import Blueprint, request, jsonify, render_template
import whisper, tempfile, os

from app.services.service_detector import detect_service
from app.services.sop_engine import load_sop_by_service_name
from app.models.service_checklist import ServiceChecklist

service_bp = Blueprint("service", __name__)
model = None

def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model("base")
    return model


# === AUDIO + SOP DEBUG ===
@service_bp.route("/debug-audio-sop", methods=["POST"])
def debug_audio_sop():
    if "audio" not in request.files:
        return jsonify({"error": "audio file required"}), 400

    audio = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio.save(tmp.name)
        tmp_path = tmp.name

    result = model.transcribe(tmp_path, language="id")
    os.remove(tmp_path)

    transcript = result["text"]
    service_key, service_name = detect_service(transcript)

    if not service_name:
        return jsonify({
            "transcript": transcript,
            "service_detected": None,
            "sop": None
        })

    sop = load_sop_by_service_name(service_name)

    return jsonify({
        "transcript": transcript,
        "service_key": service_key,
        "service_name": service_name,
        "sop": sop
    })


# === JSON API for checklist ===
@service_bp.route("/checklist/<session_id>")
def get_checklist(session_id):
    items = ServiceChecklist.query.filter_by(
        service_record_id=session_id
    ).all()

    return jsonify([item.to_dict() for item in items])

# === HTML page ===
@service_bp.route("/page/checklist/<session_id>")
def checklist_page(session_id):
    return render_template("checklist.html", session_id=session_id)