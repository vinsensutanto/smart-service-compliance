# app/services/session_manager.py

from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.workstation import Workstation
from app.models.service_checklist import ServiceChecklist
from app.services.session_store import finalize_session
from flask_login import current_user


# ======================================================
# START SESSION
# ======================================================
def start_session(
    session_id: str,
    rp_id: str,
    user_id: Optional[str] = None,
    start_time=None
) -> Optional[str]:
    """
    Start a new session for a workstation (RP). 
    Only attach user_id if provided explicitly.
    Prevents multiple active sessions per workstation.
    """
    rp_id = rp_id.upper()
    start_time = start_time or datetime.now(timezone.utc)

    # Resolve workstation
    workstation = db.session.query(Workstation).filter_by(rpi_id=rp_id).first()
    if not workstation:
        print(f"[SESSION] Unknown rp_id={rp_id}")
        return None

    # Check for existing active session
    active = (
        db.session.query(ServiceRecord)
        .filter(
            ServiceRecord.workstation_id == workstation.workstation_id,
            ServiceRecord.end_time.is_(None)
        )
        .first()
    )

    if active:
        print(f"[SESSION] Already active SR={active.service_record_id}")
        # Attach user only if explicitly provided
        if active.user_id is None and user_id is not None:
            active.user_id = user_id
            db.session.commit()
            print(f"[SESSION] Attached user {user_id} to active SR={active.service_record_id}")
        return active.service_record_id

    # Generate new service_record_id
    last = db.session.query(ServiceRecord).order_by(ServiceRecord.service_record_id.desc()).first()
    new_id = ServiceRecord.generate_id(last.service_record_id if last else None)

    # Create new session record
    record = ServiceRecord(
        service_record_id=new_id,
        workstation_id=workstation.workstation_id,
        user_id=user_id,
        start_time=start_time
    )

    db.session.add(record)
    db.session.commit()
    print(f"[SESSION] Started SR={new_id} rp={rp_id} user_id={user_id}")
    return new_id


# ======================================================
# END SESSION (SAFE + GUARDED)
# ======================================================

def end_session_by_rp(
    rp_id: str,
    manual_termination: bool = False,
    reason: Optional[str] = None
) -> Optional[str]:

    rp_id = rp_id.upper()

    record = (
        db.session.query(ServiceRecord)
        .select_from(ServiceRecord)
        .join(
            Workstation,
            ServiceRecord.workstation_id == Workstation.workstation_id
        )
        .filter(
            Workstation.rpi_id == rp_id,
            ServiceRecord.end_time.is_(None)
        )
        .order_by(ServiceRecord.start_time.desc())
        .first()
    )

    if not record:
        print(f"[SESSION] No active session for rp={rp_id}")
        return None

    # HARD GUARD (normal flow)
    if not manual_termination:
        unchecked = (
            db.session.query(ServiceChecklist)
            .filter_by(
                service_record_id=record.service_record_id,
                is_checked=False
            )
            .count()
        )

        if unchecked > 0:
            print(
                f"[SESSION] END BLOCKED SR={record.service_record_id} "
                f"unchecked={unchecked}"
            )
            return None

    finalize_session(
        service_record_id=record.service_record_id,
        manual_termination=manual_termination,
        reason=reason
    )

    return record.service_record_id

# ======================================================
# QUERY HELPERS
# ======================================================

def get_active_session_by_rp(rp_id: str) -> Optional[str]:
    rp_id = rp_id.upper()

    record = (
        db.session.query(ServiceRecord)
        .select_from(ServiceRecord)
        .join(
            Workstation,
            ServiceRecord.workstation_id == Workstation.workstation_id
        )
        .filter(
            Workstation.rpi_id == rp_id,
            ServiceRecord.end_time.is_(None)
        )
        .order_by(ServiceRecord.start_time.desc())
        .first()
    )

    return record.service_record_id if record else None


def is_checklist_complete(service_record_id: str) -> bool:
    """
    Checklist is complete if:
    - Checklist rows exist
    - All rows are checked
    """

    total = (
        db.session.query(ServiceChecklist)
        .filter(ServiceChecklist.service_record_id == service_record_id)
        .count()
    )

    if total == 0:
        return False  # SOP not initialized yet

    checked = (
        db.session.query(ServiceChecklist)
        .filter(
            ServiceChecklist.service_record_id == service_record_id,
            ServiceChecklist.is_checked.is_(True)
        )
        .count()
    )

    return total == checked

def attach_user_to_active_session(rp_id: str, user_id: str):
    from app.models.service_record import ServiceRecord
    from app.models.workstation import Workstation

    print(f"[DEBUG] Attaching user {user_id} to active session on RP={rp_id}")

    # look for the latest session for this RP without user_id
    record = (
        db.session.query(ServiceRecord)
        .join(Workstation, ServiceRecord.workstation_id == Workstation.workstation_id)
        .filter(
            Workstation.rpi_id == rp_id,
            ServiceRecord.user_id.is_(None)
        )
        .order_by(ServiceRecord.start_time.desc())
        .first()
    )

    if not record:
        print(f"[DEBUG] No session found to attach user for RP={rp_id}")
        return None

    record.user_id = user_id
    db.session.commit()
    print(f"[DEBUG] User {user_id} attached to SR={record.service_record_id}")
