from app.models import SOPService, SOPStep
from sqlalchemy.orm import Session as DBSession

def classify_service(session_text: str, db: DBSession):
    """Classify service based on session text by searching keywords in sop_steps"""
    session_text = session_text.lower()
    services = db.query(SOPService).all()

    for service in services:
        steps = db.query(SOPStep).filter_by(service_id=service.service_id).all()
        for step in steps:
            if step.step_description.lower() in session_text:
                return {
                    "service_detected": service.service_name,
                    "confidence": 0.9,  # optionally adjust
                    "detected_keywords": [step.step_description[:20]]  # example snippet
                }
    # fallback
    return {"service_detected": "unknown", "confidence": 0, "detected_keywords": []}

def get_sop_for_service(service_name: str, db: DBSession):
    service = db.query(SOPService).filter_by(service_name=service_name).first()
    if not service:
        return []

    steps = db.query(SOPStep).filter_by(service_id=service.service_id).order_by(SOPStep.step_number).all()
    return [
        {
            "step_id": step.step_id,
            "step": step.step_number,
            "description": step.step_description,
            "checked": False
        }
        for step in steps
    ]
