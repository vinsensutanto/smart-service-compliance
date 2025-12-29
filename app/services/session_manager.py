# app/services/session_manager.py

from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.workstation import Workstation
from app.models.service_checklist import ServiceChecklist


# ======================================================
# START SESSION
# ======================================================

def start_session(
    session_id: str,
    rp_id: str,
    user_id: Optional[str] = None,
    start_time=None
) -> Optional[str]:

    rp_id = rp_id.upper()
    start_time = start_time or datetime.now(timezone.utc)

    # Resolve workstation
    workstation = (
        db.session.query(Workstation)
        .filter_by(rpi_id=rp_id)
        .first()
    )

    if not workstation:
        print(f"[SESSION] Unknown rp_id={rp_id}")
        return None

    # Prevent double active session per RP
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
        return active.service_record_id

    # Generate new service_record_id
    last = (
        db.session.query(ServiceRecord)
        .order_by(ServiceRecord.service_record_id.desc())
        .first()
    )

    new_id = ServiceRecord.generate_id(
        last.service_record_id if last else None
    )

    record = ServiceRecord(
        service_record_id=new_id,
        workstation_id=workstation.workstation_id,
        user_id=user_id,
        start_time=start_time
    )

    db.session.add(record)
    db.session.commit()

    print(f"[SESSION] Started SR={new_id} rp={rp_id}")

    return new_id


# ======================================================
# END SESSION (GUARDED)
# ======================================================

def end_session_by_rp(
    rp_id: str,
    end_time=None,
    reason: Optional[str] = None
) -> Optional[str]:
    """
    Ends active session for RP.

    - Normal end: requires all checklist items completed
    - Forced end: allowed even if checklist incomplete
    """

    rp_id = rp_id.upper()
    end_time = end_time or datetime.now(timezone.utc)

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

    checklist_complete = is_checklist_complete(record.service_record_id)

    # HARD GUARD
    if not checklist_complete:
        print(
            f"[SESSION BLOCKED] SR={record.service_record_id} "
            f"Checklist incomplete"
        )
        return None

    # Set end metadata
    record.end_time = end_time

    if checklist_complete:
        record.is_normal_flow = 1
    else:
        record.is_normal_flow = 0
        record.reason = reason or "Manual termination (checklist incomplete)"

    db.session.commit()

    print(
        f"[SESSION ENDED] SR={record.service_record_id} "
        f"normal_flow={record.is_normal_flow}"
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
        .filter_by(service_record_id=service_record_id)
        .count()
    )

    if total == 0:
        return False  # SOP not initialized yet

    checked = (
        db.session.query(ServiceChecklist)
        .filter_by(
            service_record_id=service_record_id,
            is_checked=True
        )
        .count()
    )

    return total == checked