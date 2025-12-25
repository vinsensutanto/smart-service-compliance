# app/services/session_store.py
from datetime import datetime
from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.service_chunk import ServiceChunk
from app.models.service_checklist import ServiceChecklist


# ----------------------------
# ID Generators (KEEP for child tables)
# ----------------------------
def generate_chunk_id():
    last = ServiceChunk.query.order_by(ServiceChunk.chunk_id.desc()).first()
    if not last:
        return "CH0001"
    return f"CH{int(last.chunk_id[2:]) + 1:04d}"[:6]


def generate_checklist_id():
    last = ServiceChecklist.query.order_by(ServiceChecklist.checklist_id.desc()).first()
    if not last:
        return "CE0001"
    return f"CE{int(last.checklist_id[2:]) + 1:04d}"[:6]


# ----------------------------
# Persist session (UPDATE ONLY)
# ----------------------------
def persist_session(session):
    record = ServiceRecord.query.get(session.service_record_id)
    if not record:
        raise RuntimeError("ServiceRecord not found for session")

    # 🔹 update main record
    record.end_time = session.end_time
    record.duration = session.duration_sec
    record.service_detected = session.service_detected
    record.confidence = session.confidence
    record.text = " ".join(session.text_chunks)
    record.is_normal_flow = all(
        c.get("checked", False) for c in session.checklist
    )
    record.audio_path = f"local/aud/{session.service_record_id}"

    # 🔹 save chunks
    for text in session.audio_chunks:
        db.session.add(ServiceChunk(
            chunk_id=generate_chunk_id(),
            service_record_id=session.service_record_id,
            text_chunk=text,
            created_at=datetime.utcnow()
        ))

    # 🔹 save checklist
    for step in session.checklist:
        db.session.add(ServiceChecklist(
            checklist_id=generate_checklist_id(),
            service_record_id=session.service_record_id,
            step_id=step["step_id"],
            is_checked=step.get("checked", False),
            checked_at=step.get("checked_at")
        ))

    db.session.commit()

    print(
        f"[SESSION SAVED] {session.service_record_id} | "
        f"duration={session.duration_sec}s | "
        f"chunks={len(session.audio_chunks)} | "
        f"checklist={len(session.checklist)}"
    )
