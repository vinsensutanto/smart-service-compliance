from datetime import datetime
from app.extensions import socketio, db
from app.services.session_manager import active_sessions
from app.models.service_checklist import ServiceChecklist
from app.models.service_record import ServiceRecord
from app.services.sop_engine import load_sop_by_service_id


@socketio.on('checklist_update')
def handle_checklist_update(data):
    session_id = data.get("session_id")
    step_id = data.get("step_id")
    checked = data.get("checked", False)
    timestamp = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M")

    # 1. Cari session di memori
    session = next((s for s in active_sessions.values() if s.session_id == session_id), None)
    
    if session:
        # 2. Update status checklist di memori
        for step in session.checklist:
            if step["step_id"] == step_id:
                step["checked"] = checked
                step["checked_at"] = timestamp
                break

        # 3. Emit data terbaru ke Dashboard
        socketio.emit("sop_update", {
            "session_id": session_id, 
            "service": session.service_detected,
            "confidence": session.confidence,
            "sop": session.checklist
        })

        # 4. Update Database (Sekarang aman di dalam blok 'if session')
        service_record = db.session.query(ServiceRecord)\
            .filter_by(service_record_id=session.service_record_id)\
            .first()
            
        if service_record:
            sc = db.session.query(ServiceChecklist)\
                .filter_by(service_record_id=service_record.service_record_id, step_id=step_id)\
                .first()
            if sc:
                sc.is_checked = checked
                sc.checked_at = timestamp
                db.session.commit()

def initialize_checklist(session_id, service_record_id, service_id):
    sop = load_sop_by_service_id(service_id)
    if not sop:
        return

    checklist = []

    for step in sop["steps"]:
        sc = ServiceChecklist(
            service_record_id=service_record_id,
            step_id=step["step_id"],
            description=step["step_description"],
            is_checked=False
        )
        db.session.add(sc)

        checklist.append({
            "step_id": step["step_id"],
            "description": step["step_description"],
            "checked": False,
            "checked_at": None
        })

    db.session.commit()
    active_sessions[session_id].checklist = checklist

    socketio.emit("sop_update", {
        "session_id": session_id,
        "service": active_sessions[session_id].service_detected,
        "confidence": active_sessions[session_id].confidence,
        "sop": checklist
    })
