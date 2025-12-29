# app/routes/checklist_routes.py

from datetime import datetime
from app.extensions import socketio, db
from app.services.session_manager import get_active_session_by_rp
from app.models.service_checklist import ServiceChecklist
from app.models.service_record import ServiceRecord
from app.services.sop_engine import load_sop_by_service_id
import logging
from app.models.sop_step import SOPStep

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_checklist_id(last_id=None):
    """Generate incremental checklist_id like CE0001, CE0002, ..."""
    if not last_id:
        return "CE0001"
    num = int(last_id[2:]) + 1
    return f"CE{num:04d}"


@socketio.on('checklist_update')
def handle_checklist_update(data):
    """
    Handle frontend checkbox updates via SocketIO.
    Auto-initialize checklist if missing.
    """
    print("[SOCKET] checklist_update received:", data)

    session_id = data.get("session_id")
    step_id = data.get("step_id")
    checked = data.get("checked", False)
    timestamp = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M")

    logger.info(f"[SocketIO] checklist_update received: session_id={session_id}, step_id={step_id}, checked={checked}")

    # 1. Resolve service record
    service_record = db.session.query(ServiceRecord).filter_by(service_record_id=session_id).first()
    if not service_record:
        # fallback: session_id may be RP ID
        sr_id = get_active_session_by_rp(session_id)
        if not sr_id:
            logger.warning(f"[SESSION] No active session found for session_id/rp_id={session_id}")
            return
        service_record = db.session.query(ServiceRecord).filter_by(service_record_id=sr_id).first()

    # 2. Ensure checklist exists
    sc = db.session.query(ServiceChecklist).filter_by(
        service_record_id=service_record.service_record_id,
        step_id=step_id
    ).first()
    if not sc:
        logger.info(f"[DB] Checklist missing for SR={service_record.service_record_id}, initializing...")
        initialize_checklist(service_record.service_record_id, getattr(service_record, "service_id", None))
        sc = db.session.query(ServiceChecklist).filter_by(
            service_record_id=service_record.service_record_id,
            step_id=step_id
        ).first()
        if not sc:
            logger.error(f"[DB] Failed to initialize checklist for step_id={step_id}")
            return

    # 3. Update DB
    sc.is_checked = checked
    sc.checked_at = timestamp
    db.session.commit()
    logger.info(f"[DB] Step updated in DB: {step_id}, checked={checked}")

    # 4. Emit updated checklist to frontend
    emit_checklist(service_record.service_record_id)


def initialize_checklist(service_record_id, service_id):
    """
    Initialize the SOP checklist for a service record.
    Commits to DB and emits to frontend.
    """
    sop = load_sop_by_service_id(service_id)
    if not sop:
        logger.warning(f"[INIT] SOP not found for service_id={service_id}")
        return

    checklist = []

    # Get last checklist_id from DB
    last = db.session.query(ServiceChecklist).order_by(ServiceChecklist.checklist_id.desc()).first()
    last_id = last.checklist_id if last else None

    for step in sop["steps"]:
        sc_id = generate_checklist_id(last_id)
        last_id = sc_id  # next iteration

        sc = ServiceChecklist(
            checklist_id=sc_id,
            service_record_id=service_record_id,
            step_id=step["step_id"],
            is_checked=False
        )
        db.session.add(sc)

        checklist.append({
            "step_id": step["step_id"],
            "description": step.get("step_description", ""),
            "checked": False,
            "checked_at": None
        })

    db.session.commit()
    logger.info(f"[INIT] Checklist initialized for SR={service_record_id}")

    # Emit initial checklist to frontend
    emit_checklist(service_record_id)


def emit_checklist(service_record_id):
    """
    Fetch checklist from DB and emit via SocketIO.
    """
    service_record = db.session.query(ServiceRecord).filter_by(service_record_id=service_record_id).first()
    if not service_record:
        return

    rows = (
        db.session.query(ServiceChecklist, SOPStep)
        .join(SOPStep, SOPStep.step_id == ServiceChecklist.step_id)
        .filter(ServiceChecklist.service_record_id == service_record_id)
        .order_by(SOPStep.step_number)
        .all()
    )

    sop_payload = [
        {
            "step_id": sc.step_id,
            "description": step.step_description,
            "checked": sc.is_checked,
            "checked_at": sc.checked_at.strftime("%Y-%m-%d %H:%M") if sc.checked_at else None
        }
        for sc, step in rows
    ]

    socketio.emit("sop_update", {
        "session_id": service_record.service_record_id,
        "service": getattr(service_record, "service_detected", None),
        "confidence": getattr(service_record, "confidence", None),
        "sop": sop_payload
    })
