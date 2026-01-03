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
from scripts.stt_whisper import transcribe_chunk
import re

import soundfile as sf
import numpy as np

# =====================================
# CONFIG
# =====================================
MQTT_BROKER = "10.159.121.208"
MQTT_PORT = 1883

AUDIO_TOPIC = "rp/+/audio/stream"
KWS_TOPIC = "rp/+/event/kws/+"

audio_queue = queue.Queue()
model = get_whisper_model()

SERVICE_KEY_MAP = {
    "MBCA_REGISTRATION": "SV0003",
    "OPEN_ACCOUNT": "SV0002",
    "ATM_REPLACEMENT": "SV0001",
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
    app = userdata["app"]

    if parts[2] == "event" and parts[3] == "kws":
        if len(parts) < 5:
            print("[INGESTOR] Invalid KWS topic:", msg.topic)
            return

        event_type = parts[4].lower()
        payload["event"] = event_type 

        with app.app_context():
            handle_kws_event(rp_id, payload)
        return

    if parts[2] == "audio" and parts[3] == "stream":
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
    audio_b64 = payload.get("audio")

    if not isinstance(chunk_number, int):
        print("[AUDIO] Invalid chunk_number")
        return

    if not audio_b64:
        print("[AUDIO] Missing audio")
        return

    print(f"[AUDIO] queued SR={sr_id} rp={rp_id} chunk={chunk_number}")

    # ---------------------------------
    # Decode audio → temp mp3
    # ---------------------------------
    audio_bytes = base64.b64decode(audio_b64)
    # with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
    #     tmp.write(audio_bytes)
    #     tmp_path = tmp.name
    # audio_b64 = payload.get("audio")
    fmt = payload.get("format")
    sr = payload.get("sample_rate", 16000)

    if fmt != "pcm_s16le":
        print("[AUDIO] Unsupported format:", fmt)
        return

    pcm = np.frombuffer(base64.b64decode(audio_b64), dtype=np.int16)

    # if len(pcm) < sr * 1:   # < 1 detik
    #     return

    audio_float = pcm.astype(np.float32) / 32768.0

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio_float, sr)
        tmp_path = tmp.name

    # ---------------------------------
    # Speech-to-text
    # ---------------------------------
    # result = model.transcribe(tmp_path, language="id", verbose=False)
    # text = result.get("text", "").strip()

    # ---------------------------------
    # Append to service_records.text
    # ---------------------------------
    record = db.session.get(ServiceRecord, sr_id)
    if not record:
        print(f"[AUDIO] ServiceRecord not found: {sr_id}")
        return

    text = transcribe_chunk(
        tmp_path,
        language="id"
    )

    text = normalize_whisper_text(text)
    
    if not text:
        return
    
    service_already_locked = bool(record.service_id)

    # Append transcript
    record.text = f"{record.text} {text}" if record.text else text
    db.session.commit()

    full_text = record.text

    # ---------------------------------
    # EARLY SERVICE DETECTION (ONE-SHOT)
    # ---------------------------------
    if not service_already_locked:
        recent_text = " ".join(record.text.split()[-30:])
        service_key, label, confidence, hits = detect_service(recent_text)

        if service_key and should_lock_service(service_key, confidence):
            service_id = SERVICE_KEY_MAP.get(service_key)
            if service_id:
                record.service_id = service_id
                record.service_detected = label
                record.confidence = confidence

                db.session.commit()

                print(
                    f"[SERVICE LOCKED] SR={sr_id} "
                    f"{label} conf={confidence}"
                )

                # INIT SOP
                from app.routes.checklist_routes import initialize_checklist
                initialize_checklist(sr_id, service_id)

                # EMIT TO UI
                from app.services.payload_builder import build_session_payload
                from app.extensions import socketio

                payload = build_session_payload(sr_id)
                payload["rp_id"] = rp_id
                socketio.emit("service_locked", payload)
                socketio.emit("sop_update", payload)

    # ---------------------------------
    # Save chunk audit
    last_chunk = (
        db.session.query(ServiceChunk)
        .filter(ServiceChunk.service_record_id == sr_id)
        .order_by(ServiceChunk.chunk_id.desc())
        .first()
    )

    chunk_id = ServiceChunk.generate_id(
        last_chunk.chunk_id if last_chunk else None
    )
    
    MAX_CHUNK_LEN = 254

    chunks = split_text(text, MAX_CHUNK_LEN)

    last_chunk = (
        db.session.query(ServiceChunk)
        .order_by(ServiceChunk.chunk_id.desc())
        .first()
    )

    prev_chunk_id = last_chunk.chunk_id if last_chunk else None

    for part in chunks:
        new_chunk_id = ServiceChunk.generate_id(prev_chunk_id)

        chunk = ServiceChunk(
            chunk_id=new_chunk_id,
            service_record_id=sr_id,
            text_chunk=part,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(chunk)
        prev_chunk_id = new_chunk_id

    db.session.commit()

    print(f"[DB] {len(chunks)} chunks saved SR={sr_id}")



# =====================================
# START INGESTOR
# =====================================
def start_ingestor(app):
    print("[INGESTOR] Connecting to MQTT...", MQTT_BROKER, MQTT_PORT)
    client = mqtt.Client(userdata={"app": app})
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(AUDIO_TOPIC)
    client.subscribe(KWS_TOPIC)

    print("[INGESTOR] subscribed:", AUDIO_TOPIC, KWS_TOPIC)

    threading.Thread(
        target=audio_worker,
        args=(app,),
        daemon=True
    ).start()

    client.loop_start()

    print("[INGESTOR] audio ingestor READY")

def split_text(text, max_len):
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

def normalize_whisper_text(text: str) -> str:
    # text = text.replace("...", ",")
    # text = text.replace("..", ",")
    # text = text.replace(" .", ".")
    # text = re.sub(r"\s+,", ",", text)
    # text = re.sub(r"\s+\.", ".", text)
    # text = re.sub(r"\s{2,}", " ", text)
    return text.strip()