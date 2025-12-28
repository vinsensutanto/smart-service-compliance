import base64
import json
import queue
import tempfile
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from app.extensions import db
from app.models.service_chunk import ServiceChunk
from app.models.service_record import ServiceRecord
from app.services.session_manager import get_active_session_by_rp
from app.services.whisper_model import get_whisper_model
from app.services.service_detector import detect_service, should_lock_service
from app.services.sop_engine import load_sop_by_service_id
from app.services.kws_event_handler import handle_kws_event


# =====================================
# CONFIG
# =====================================
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

AUDIO_TOPIC = "rp/+/audio/stream"
KWS_TOPIC = "rp/+/event/kws"

audio_queue = queue.Queue()
model = get_whisper_model()

SERVICE_KEY_MAP = {
    "MBCA_REGISTRATION": "SV0003",
    "OPEN_ACCOUNT": "SV0001",
    "ATM_REPLACEMENT": "SV0002",
}


# =====================================
# MQTT CALLBACK
# =====================================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception as e:
        print("[INGESTOR] Invalid JSON:", e)
        return

    parts = msg.topic.split("/")
    if len(parts) < 4:
        print("[INGESTOR] Invalid topic:", msg.topic)
        return

    rp_id = parts[1].upper()
    channel = parts[2]
    event_type = parts[3]

    app = userdata["app"]

    # -----------------------------
    # KWS EVENT
    # -----------------------------
    if channel == "event" and event_type == "kws":
        with app.app_context():
            handle_kws_event(rp_id, payload)
        return

    # -----------------------------
    # AUDIO STREAM
    # -----------------------------
    if channel == "audio" and event_type == "stream":
        audio_queue.put((rp_id, payload))
        return


# =====================================
# AUDIO WORKER THREAD
# =====================================
def audio_worker(app):
    with app.app_context():
        while True:
            rp_id, payload = audio_queue.get()
            try:
                process_audio_chunk(rp_id, payload)
            except Exception as e:
                print("[INGESTOR] processing error:", e)
            finally:
                audio_queue.task_done()


# =====================================
# CORE AUDIO PROCESSOR
# =====================================
def process_audio_chunk(rp_id: str, payload: dict):
    db.session.remove()
    sr_id = get_active_session_by_rp(rp_id)
    if not sr_id:
        print(f"[AUDIO] No active session for rp={rp_id}")
        return

    chunk_number = payload.get("chunk_number")
    audio_b64 = payload.get("audio_base64")

    if not audio_b64:
        print("[AUDIO] Missing audio_base64")
        return

    print(f"[AUDIO] queued SR={sr_id} rp={rp_id} chunk={chunk_number}")

    # ---------------------------------
    # Decode audio → temp mp3
    # ---------------------------------
    audio_bytes = base64.b64decode(audio_b64)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # ---------------------------------
    # Speech-to-text
    # ---------------------------------
    result = model.transcribe(tmp_path, language="id", verbose=False)
    text = result.get("text", "").strip()

    if not text:
        return

    # ---------------------------------
    # Append to service_records.text
    # ---------------------------------
    record = db.session.get(ServiceRecord, sr_id)
    if not record:
        print(f"[AUDIO] ServiceRecord not found: {sr_id}")
        return

    record.text = f"{record.text} {text}" if record.text else text
    db.session.commit()

    full_text = record.text

    # ---------------------------------
    # EARLY SERVICE DETECTION
    # ---------------------------------
    if not record.service_id:
        service_key, label, confidence, hits = detect_service(full_text)

        if service_key and should_lock_service(confidence):
            service_id = SERVICE_KEY_MAP.get(service_key)
            if service_id:
                record.service_id = service_id
                record.service_detected = label
                record.confidence = confidence
                db.session.commit()

                load_sop_by_service_id(service_id)

                print(
                    f"[SERVICE LOCKED] SR={sr_id} "
                    f"{label} conf={confidence}"
                )

    # ---------------------------------
    # Save chunk audit
    # ---------------------------------
    last_chunk = (
        db.session.query(ServiceChunk)
        .order_by(ServiceChunk.chunk_id.desc())
        .first()
    )

    chunk_id = ServiceChunk.generate_id(
        last_chunk.chunk_id if last_chunk else None
    )

    chunk = ServiceChunk(
        chunk_id=chunk_id,
        service_record_id=sr_id,
        text_chunk=text,
        created_at=datetime.now(timezone.utc)
    )

    db.session.add(chunk)
    db.session.commit()

    print(f"[DB] chunk saved {chunk_id} SR={sr_id}")


# =====================================
# START INGESTOR
# =====================================
def start_ingestor(app):
    client = mqtt.Client(userdata={"app": app})
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(AUDIO_TOPIC)
    client.subscribe(KWS_TOPIC)

    threading.Thread(
        target=audio_worker,
        args=(app,),
        daemon=True
    ).start()

    client.loop_start()

    print("[INGESTOR] audio ingestor READY")
