# app/services/session_store.py
from datetime import datetime
from app.extensions import db
from app.models.service_record import ServiceRecord
from app.models.service_chunk import ServiceChunk
from app.models.service_checklist import ServiceChecklist

# ----------------------------
# ID Generators
# ----------------------------
def generate_service_record_id():
    last = db.session.query(ServiceRecord).order_by(ServiceRecord.service_record_id.desc()).first()
    if not last:
        return "SR0001"
    last_num = int(last.service_record_id[2:])
    return f"SR{last_num + 1:04d}"[:6]


def generate_chunk_id():
    last = db.session.query(ServiceChunk).order_by(ServiceChunk.chunk_id.desc()).first()
    if not last:
        return "CH0001"
    last_num = int(last.chunk_id[2:])
    return f"CH{last_num + 1:04d}"[:6]


def generate_checklist_id():
    last = db.session.query(ServiceChecklist).order_by(ServiceChecklist.checklist_id.desc()).first()
    if not last:
        return "CE0001"
    last_num = int(last.checklist_id[2:])
    return f"CE{last_num + 1:04d}"[:6]


# ----------------------------
# Persist session
# ----------------------------
def persist_session(session):
    # 1️⃣ Save ServiceRecord
    service_record_id = generate_service_record_id()
    record = ServiceRecord(
        service_record_id=service_record_id,
        workstation_id=session.workstation_id[:6].upper() if session.workstation_id else "RP01",
        user_id=session.user_id[:6] if session.user_id else "unknow",
        service_detected=session.service_detected,
        confidence=session.confidence,
        start_time=session.start_time,  # <-- fixed
        end_time=session.end_time,      # <-- fixed
        duration=session.duration_sec,
        text=session.text.strip(),
        is_normal_flow=all([c.get("checked", False) for c in session.checklist]),
        reason=None,
        audio_path=f"local/aud/{service_record_id}",
    )
    db.session.add(record)
    db.session.commit()

    # 2️⃣ Save ServiceChunks
    for chunk_text in session.audio_chunks:
        chunk_id = generate_chunk_id()
        db.session.add(ServiceChunk(
            chunk_id=chunk_id,
            service_record_id=service_record_id,
            text_chunk=chunk_text,
            created_at=datetime.now()
        ))

    # 3️⃣ Save ServiceChecklists
    for step in session.checklist:
        checklist_id = generate_checklist_id()
        db.session.add(ServiceChecklist(
            checklist_id=checklist_id,
            service_record_id=service_record_id,
            step_id=step["step_id"],
            is_checked=step.get("checked", False),
            checked_at=step.get("checked_at")
        ))

    db.session.commit()

    print(
        f"[SESSION SAVED] {service_record_id} | "
        f"duration={session.duration_sec}s | "
        f"chunks={len(session.audio_chunks)} | "
        f"checklist={len(session.checklist)}"
    )
