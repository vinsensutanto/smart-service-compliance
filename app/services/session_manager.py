# app/services/session_manager.py

from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.workstation import Workstation


def start_session(
    session_id: str,
    rp_id: str,
    user_id: Optional[str] = None,
    start_time=None
) -> Optional[str]:

    rp_id = rp_id.upper()
    start_time = start_time or datetime.now(timezone.utc)

    # resolve workstation
    workstation = (
        db.session.query(Workstation)
        .filter_by(rpi_id=rp_id)
        .first()
    )

    if not workstation:
        print(f"[SESSION] Unknown rp_id={rp_id}")
        return None

    # prevent double active session per RP
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


def end_session_by_rp(
    rp_id: str,
    end_time=None,
    reason=None
) -> Optional[str]:

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

    record.end_time = end_time
    if reason:
        record.reason = reason

    db.session.commit()

    print(f"[SESSION] Ended SR={record.service_record_id} rp={rp_id}")

    return record.service_record_id


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
