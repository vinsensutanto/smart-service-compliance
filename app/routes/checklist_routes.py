from datetime import datetime
from app.extensions import socketio, db
from app.services.session_manager import active_sessions
from app.models.service_checklist import ServiceChecklist
from app.models.service_record import ServiceRecord

@socketio.on('checklist_update')
def handle_checklist_update(data):
    session_id = data.get("session_id")
    step_id = data.get("step_id")
    checked = data.get("checked", False)
    timestamp = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---------------------------
    # 1️⃣ Update in-memory session
    # ---------------------------
    session = next((s for s in active_sessions.values() if s.session_id == session_id), None)
    if session:
        for step in session.checklist:
            if step["step_id"] == step_id:
                step["checked"] = checked
                step["checked_at"] = timestamp
                break

        # Emit updated checklist to all connected UIs
        socketio.emit("sop_update", {"session_id": session_id, "checklist": session.checklist})

    # ---------------------------
    # 2️⃣ Persist to DB (optional real-time)
    # ---------------------------
    # If session has already a ServiceRecord in DB
    service_record = db.session.query(ServiceRecord)\
        .filter_by(service_record_id=session_id)\
        .first()
    if service_record:
        sc = db.session.query(ServiceChecklist)\
            .filter_by(service_record_id=service_record.service_record_id, step_id=step_id)\
            .first()
        if sc:
            sc.is_checked = checked
            sc.checked_at = timestamp
            db.session.commit()
