from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.sop_step import SOPStep
from app.models.service_checklist import ServiceChecklist


def build_session_payload(service_record_id: str):
    sr = ServiceRecord.query.filter_by(
        service_record_id=service_record_id
    ).first()

    if not sr:
        return None

    checklist = (
        db.session.query(SOPStep, ServiceChecklist)
        .outerjoin(
            ServiceChecklist,
            (ServiceChecklist.step_id == SOPStep.step_id) &
            (ServiceChecklist.service_record_id == sr.service_record_id)
        )
        .filter(SOPStep.service_id == sr.service_id)
        .order_by(SOPStep.step_number)
        .all()
    )

    return {
        "session_id": sr.service_record_id,
        "service_record_id": sr.service_record_id,
        "service": sr.service_detected,
        "confidence": sr.confidence or 0,
        "sop": [
            {
                "step_id": step.step_id,
                "description": step.step_description,
                "checked": sc.is_checked if sc else False
            }
            for step, sc in checklist
        ]
    }
