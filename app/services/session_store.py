# app/services/session_store.py

from datetime import datetime, timezone
from sqlalchemy import func

from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.service_chunk import ServiceChunk
from app.models.service_checklist import ServiceChecklist


# =========================================
# ID generators (KEEP)
# =========================================
def generate_checklist_id():
    last = (
        db.session.query(ServiceChecklist)
        .order_by(ServiceChecklist.checklist_id.desc())
        .first()
    )
    if not last:
        return "CE0001"
    return f"CE{int(last.checklist_id[2:]) + 1:04d}"


# =========================================
# Session finalization
# =========================================
def finalize_session(
    service_record_id: str,
    manual_termination: bool = False,
    reason: str | None = None
):
    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )
    if not record:
        raise RuntimeError("ServiceRecord not found")

    if record.end_time:
        return

    if manual_termination:
        record.is_normal_flow = False
        record.reason = reason or "Manual termination by supervisor"
    else:
        unchecked = (
            db.session.query(ServiceChecklist)
            .filter_by(
                service_record_id=service_record_id,
                is_checked=False
            )
            .count()
        )

        if unchecked == 0:
            record.is_normal_flow = True
            record.reason = None
        else:
            record.is_normal_flow = False
            record.reason = "SOP not completed"

    record.end_time = datetime.now(timezone.utc)

    if record.start_time:
        start = record.start_time
        end = record.end_time

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        record.duration = int((end - start).total_seconds())

    chunks = (
        db.session.query(ServiceChunk.text_chunk)
        .filter_by(service_record_id=service_record_id)
        .order_by(ServiceChunk.created_at.asc())
        .all()
    )

    record.text = " ".join(c.text_chunk for c in chunks)

    db.session.commit()

    print(
        f"[SESSION FINALIZED] {service_record_id} "
        f"duration={record.duration}s "
        f"normal={record.is_normal_flow}"
    )

# =========================================
# Persist checklist (from UI)
# =========================================
def save_checklist(
    service_record_id: str,
    checklist_items: list[dict]
):
    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )
    if not record:
        raise RuntimeError("ServiceRecord not found")

    db.session.query(ServiceChecklist)\
        .filter_by(service_record_id=service_record_id)\
        .delete()

    for step in checklist_items:
        db.session.add(ServiceChecklist(
            checklist_id=generate_checklist_id(),
            service_record_id=service_record_id,
            step_id=step["step_id"],
            is_checked=step.get("checked", False),
            checked_at=step.get("checked_at")
        ))

    db.session.commit()

    print(
        f"[CHECKLIST SAVED] {service_record_id} "
        f"steps={len(checklist_items)}"
    )
