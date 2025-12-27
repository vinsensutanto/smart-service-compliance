# app/services/sop_engine.py
from app.models.sop_service import SOPService
from app.models.sop_step import SOPStep
from app.extensions import db


def load_sop_by_service_id(service_id: str):
    """
    Load SOP and steps using service_id (PRIMARY, SAFE METHOD)
    """

    if not service_id:
        return None

    service = (
        db.session.query(SOPService)
        .filter_by(service_id=service_id)
        .first()
    )

    if not service:
        return None

    steps = (
        db.session.query(SOPStep)
        .filter_by(service_id=service.service_id)
        .order_by(SOPStep.step_number.asc())
        .all()
    )

    return {
        "service_id": service.service_id,
        "service_name": service.service_name,
        "steps": [
            {
                "step_id": step.step_id,
                "step_number": step.step_number,
                "step_description": step.step_description,
                "checked": False,
                "timestamp": None
            }
            for step in steps
        ]
    }
