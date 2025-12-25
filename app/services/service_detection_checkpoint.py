from app.extensions import db
from app.models.service_record import ServiceRecord
from app.services.service_detector import detect_service
from app.services.sop_engine import load_sop_by_service_name


def run_service_detection_checkpoint(service_record_id: str):
    """
    Run service detection once transcript is available
    """

    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )

    if not record or not record.full_transcript:
        return {
            "status": "error",
            "message": "Transcript not ready"
        }

    # Already detected → skip
    if record.service_name:
        sop = load_sop_by_service_name(record.service_name)
        return {
            "status": "already_detected",
            "service_name": record.service_name,
            "confidence": record.confidence,
            "sop": sop
        }

    # Detect service
    service_key, confidence, keywords = detect_service(record.full_transcript)

    if not service_key:
        return {
            "status": "not_detected"
        }

    # Save result
    record.service_name = service_key
    record.confidence = confidence
    db.session.commit()

    sop = load_sop_by_service_name(service_key)

    return {
        "status": "detected",
        "service_name": service_key,
        "confidence": confidence,
        "matched_keywords": keywords,
        "sop": sop
    }
