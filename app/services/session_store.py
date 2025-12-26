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
def finalize_session(service_record_id: str):
    """
    Close session:
    - set end_time
    - calculate duration
    - aggregate transcript
    """

    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )
    if not record:
        raise RuntimeError("ServiceRecord not found")

    if record.end_time:
        return  # already finalized

    now = datetime.now(timezone.utc)
    record.end_time = now

    if record.start_time:
        record.duration = int(
            (now - record.start_time).total_seconds()
        )

    # 🔹 aggregate transcript from chunks
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
        f"duration={record.duration}s chunks={len(chunks)}"
    )


# =========================================
# Persist checklist (from UI)
# =========================================
def save_checklist(
    service_record_id: str,
    checklist_items: list[dict]
):
    """
    checklist_items example:
    [
        {
            "step_id": "ST0001",
            "checked": true,
            "checked_at": "2025-12-25T14:33:00Z"
        }
    ]
    """

    record = (
        db.session.query(ServiceRecord)
        .filter_by(service_record_id=service_record_id)
        .first()
    )
    if not record:
        raise RuntimeError("ServiceRecord not found")

    # clear old checklist (idempotent)
    db.session.query(ServiceChecklist)\
        .filter_by(service_record_id=service_record_id)\
        .delete()

    is_normal = True

    for step in checklist_items:
        if not step.get("checked", False):
            is_normal = False

        db.session.add(ServiceChecklist(
            checklist_id=generate_checklist_id(),
            service_record_id=service_record_id,
            step_id=step["step_id"],
            is_checked=step.get("checked", False),
            checked_at=step.get("checked_at")
        ))

    record.is_normal_flow = is_normal
    db.session.commit()

    print(
        f"[CHECKLIST SAVED] {service_record_id} "
        f"steps={len(checklist_items)} normal={is_normal}"
    )
