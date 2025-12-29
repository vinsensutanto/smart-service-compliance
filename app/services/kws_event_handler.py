from datetime import datetime, timezone

from app.services.session_manager import (
    start_session,
    end_session_by_rp,
    get_active_session_by_rp
)
from app.extensions import socketio
from app.services.stream_controller import publish_end_stream
from app.services.payload_builder import build_session_payload
from app.routes.checklist_routes import initialize_checklist
from app.models.service_record import ServiceRecord
from app.extensions import db

# =====================================
# EVENT NORMALIZATION
# =====================================
START_EVENTS = {"start", "mulai", "begin"}
END_EVENTS = {"end", "selesai", "stop"}

# =====================================
# KWS EVENT HANDLER
# =====================================
def handle_kws_event(rp_id: str, payload: dict):

    raw_event = payload.get("event", "").lower()
    ts = payload.get("timestamp")

    timestamp = (
        datetime.fromisoformat(ts)
        if ts else datetime.now(timezone.utc)
    )

    rp_id = rp_id.upper()

    # ---------------------------------
    # START SESSION
    # ---------------------------------
    if raw_event in START_EVENTS:
        active = get_active_session_by_rp(rp_id)
        if active:
            print(f"[KWS] Session already active SR={active} rp={rp_id}")
            return

        sr_id = start_session(
            session_id=None,
            rp_id=rp_id,
            user_id=None,
            start_time=timestamp
        )

        if sr_id:
            print(f"[KWS] START session SR={sr_id} rp={rp_id}")
            
            sr = db.session.query(ServiceRecord).filter_by(service_record_id=sr_id).first()
            if not sr:
                print(f"[KWS] ERROR: ServiceRecord not found after start SR={sr_id}")
                return

            initialize_checklist(sr_id, sr.service_id)
            
            payload = build_session_payload(sr_id)
            if payload:
                socketio.emit("session_started", payload)
                socketio.emit("sop_update", payload)

        else:
            print(f"[KWS] Failed to start session rp={rp_id}")

        return

    # ---------------------------------
    # END SESSION
    # ---------------------------------
    if raw_event in END_EVENTS:
        sr_id = end_session_by_rp(
            rp_id=rp_id,
            manual_termination=False
        )

        if sr_id:
            publish_end_stream(sr_id)
            
            print(f"[KWS] END session SR={sr_id} rp={rp_id}")

            socketio.emit(
                "session_ended",
                {
                    "session_id": sr_id,
                    "reason": "Auto-ended (KWS selesai)"
                }
            )
        else:
            print(f"[KWS] No active session to end rp={rp_id}")

        return

    # ---------------------------------
    # UNKNOWN EVENT
    # ---------------------------------
    print(f"[KWS] Unknown event '{raw_event}' payload={payload}")
