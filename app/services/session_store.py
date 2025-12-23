import json
import os
from datetime import datetime

BASE_DIR = os.path.join("data", "sessions")
os.makedirs(BASE_DIR, exist_ok=True)


def persist_session(session):
    """
    Persist a finished session as JSON.
    Safe to replace with DB later.
    """
    path = os.path.join(BASE_DIR, f"{session.session_id}.json")

    payload = {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "workstation_id": session.workstation_id,
        "start_time": session.start_dt.isoformat(),
        "end_time": session.end_dt.isoformat() if session.end_dt else None,
        "duration_sec": session.duration,
        "audio_chunks": len(session.audio_chunks),
        "text": session.text.strip(),
        "service_detected": session.service_detected,
        "confidence": session.confidence,
        "checklist": session.checklist,
        "stored_at": datetime.now().isoformat(),
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    print(
        f"[SESSION SAVED] {session.session_id} | "
        f"duration={payload['duration_sec']}s | "
        f"chunks={payload['audio_chunks']}"
    )
