from app.extensions import db
from app.models.service_record import ServiceRecord


def generate_service_record_id():
    last = (
        db.session.query(ServiceRecord)
        .order_by(ServiceRecord.service_record_id.desc())
        .first()
    )

    if not last:
        return "SR0001"

    last_num = int(last.service_record_id[2:])
    new_id = f"SR{last_num + 1:04d}"
    return new_id[:6]



def persist_session(session):
    record_id = generate_service_record_id()
    # truncate to match DB schema
    record_id = record_id[:6]  # service_record_id VARCHAR(6)
    user_id = session.user_id[:6] if session.user_id else "unknow"
    workstation_id = session.workstation_id[:6] if session.workstation_id else "RP01"

    record = ServiceRecord(
        service_record_id=record_id,
        workstation_id=workstation_id.upper(),
        user_id=user_id,
        service_detected=session.service_detected,
        confidence=session.confidence,
        start_time=session.start_dt,
        end_time=session.end_time,
        duration=session.duration_sec,
        text=session.text,
        is_normal_flow=True,
        reason=None,
        audio_path=None,
    )


    db.session.add(record)
    db.session.commit()

    print(
        f"[SESSION SAVED] {record_id} | "
        f"duration={session.duration_sec}s | "
        f"chunks={len(session.audio_chunks)}"
    )
