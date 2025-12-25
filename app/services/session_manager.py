# app/services/session_manager.py

from datetime import datetime, timezone
from typing import Dict, Optional

from app.extensions import db
from app.models.service_record import ServiceRecord

# =========================================
# In-memory active session registry
# session_id -> service_record_id
# =========================================
active_sessions: Dict[str, str] = {}


# =========================================
# Session lifecycle helpers
# =========================================
def start_session(
    session_id: str,
    workstation_id: str,
    user_id: Optional[str] = None
) -> str:
    """
    Start a new service session.
    Creates ServiceRecord immediately.
    """

    if session_id in active_sessions:
        return active_sessions[session_id]

    last_record = (
        db.session.query(ServiceRecord)
        .order_by(ServiceRecord.service_record_id.desc())
        .first()
    )

    new_id = ServiceRecord.generate_id(
        last_record.service_record_id if last_record else None
    )

    record = ServiceRecord(
        service_record_id=new_id,
        workstation_id=workstation_id,
        user_id=user_id,
        start_time=datetime.now(timezone.utc)
    )

    db.session.add(record)
    db.session.commit()

    active_sessions[session_id] = new_id

    print(
        f"[SESSION] Started session={session_id} "
        f"service_record_id={new_id} workstation={workstation_id}"
    )

    return new_id


def end_session(session_id: str):
    """
    End a session and close ServiceRecord.
    """

    service_record_id = active_sessions.pop(session_id, None)
    if not service_record_id:
        return

    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )

    if record:
        record.end_time = datetime.now(timezone.utc)
        db.session.commit()

        print(
            f"[SESSION] Ended session={session_id} "
            f"service_record_id={service_record_id}"
        )


def get_service_record_id(session_id: str) -> Optional[str]:
    """
    Resolve session_id → service_record_id
    """
    return active_sessions.get(session_id)


def is_active(session_id: str) -> bool:
    return session_id in active_sessions
