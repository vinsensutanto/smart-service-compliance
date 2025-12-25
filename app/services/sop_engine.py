from app.models.sop_service import SOPService
from app.models.sop_step import SOPStep
from app.extensions import db

# deprecated function
def load_sop(service_name):
    sop = SOPService.query.filter_by(service_name=service_name).first()
    if not sop:
        return []

    steps = (
        SOPStep.query
        .filter_by(service_id=sop.service_id)
        .order_by(SOPStep.step_order)
        .all()
    )

    return [
        {
            "step_id": step.step_id,
            "order": step.step_order,
            "description": step.description,
            "checked": False,
            "timestamp": None
        }
        for step in steps
    ]

def load_sop_by_service_name(service_name: str):
    """
    Load SOP and its steps from DB using service_name
    """

    service = (
        db.session.query(SOPService)
        .filter_by(service_name=service_name)
        .first()
    )

    if not service:
        return None

    steps = (
        db.session.query(SOPStep)
        .filter_by(service_id=service.service_id)
        .order_by(SOPStep.step_order.asc())
        .all()
    )

    return {
        "service_id": service.service_id,
        "service_name": service.service_name,
        "steps": [
            {
                "step_id": step.step_id,
                "step_order": step.step_order,
                "description": step.description,
                "checked": False,
                "timestamp": None
            }
            for step in steps
        ]
    }