from datetime import datetime, timezone

from app.services.session_manager import (
    start_session,
    end_session_by_rp,
    get_active_session_by_rp
)

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
        else:
            print(f"[KWS] Failed to start session rp={rp_id}")

        return

    # ---------------------------------
    # END SESSION
    # ---------------------------------
    if raw_event in END_EVENTS:
        sr_id = end_session_by_rp(
            rp_id=rp_id,
            end_time=timestamp
        )

        if sr_id:
            print(f"[KWS] END session SR={sr_id} rp={rp_id}")
        else:
            print(f"[KWS] No active session to end rp={rp_id}")

        return

    print(f"[KWS] Unknown event '{raw_event}' payload={payload}")
