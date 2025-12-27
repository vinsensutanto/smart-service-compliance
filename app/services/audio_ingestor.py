import os
import queue
import tempfile
import threading
import json
import base64
from datetime import datetime, timezone
from collections import defaultdict

import paho.mqtt.client as mqtt
import whisper
import torch

from app.extensions import db
from app.models.service_chunk import ServiceChunk
from app.models.service_record import ServiceRecord
from app.services.service_detector import detect_service
from app.models.workstation import Workstation

# ===============================
# GLOBAL STATE
# ===============================

SERVICE_KEY_TO_DB_ID = {
    "ATM_REPLACEMENT": "SV0001",
    "OPEN_ACCOUNT": "SV0002",
    "MBCA_REGISTRATION": "SV0003",
}


audio_queue = queue.Queue()

# session_id -> service_record_id
active_sessions = {}

# service_record_id -> accumulated text
session_text_buffer = {}

# keyword hit counter per session
SESSION_KEYWORD_COUNT = defaultdict(int)

# prevent double start
_ingestor_started = False


# ===============================
# WHISPER CONFIG
# ===============================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

print(f"[WHISPER] device={DEVICE}, dtype={DTYPE}")

WHISPER_MODEL = whisper.load_model(
    "base",
    device=DEVICE
)


# ===============================
# INGESTOR START
# ===============================

def start_ingestor(app, broker="localhost", port=1883):
    global _ingestor_started
    if _ingestor_started:
        print("[INGESTOR] Already started, skipping")
        return

    _ingestor_started = True
    topic = "+/audio/stream"

    # ===============================
    # MQTT CALLBACKS
    # ===============================

    def on_connect(client, userdata, flags, rc):
        print(f"[INGESTOR] Connected to MQTT broker rc={rc}")
        client.subscribe(topic)
        print(f"[INGESTOR] Subscribed to topic: {topic}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload)

            audio_bytes = base64.b64decode(payload["audio_base64"])
            chunk_number = payload.get("chunk_number", 0)

            rp_id = msg.topic.split("/")[0]
            session_id = payload.get("session_id", rp_id)

            with app.app_context():
                if session_id not in active_sessions:
                    last = (
                        db.session.query(ServiceRecord)
                        .order_by(ServiceRecord.service_record_id.desc())
                        .first()
                    )

                    new_id = ServiceRecord.generate_id(
                        last.service_record_id if last else None
                    )

                    # cari workstation berdasarkan rpi_id
                    workstation = (
                        db.session.query(Workstation)
                        .filter_by(rpi_id=rp_id)
                        .first()
                    )

                    if not workstation:
                        print(f"[INGESTOR] Unknown RP ID: {rp_id}")
                        return  # stop processing this message

                    record = ServiceRecord(
                        service_record_id=new_id,
                        workstation_id=workstation.workstation_id,  # WSxxxx
                        start_time=datetime.now(timezone.utc),
                        service_detected=None,
                        service_id=None,
                        confidence=None
                    )


                    db.session.add(record)
                    db.session.commit()

                    active_sessions[session_id] = new_id
                    session_text_buffer[new_id] = ""

                    print(f"[SESSION] New session {session_id} → {new_id}")

                service_record_id = active_sessions[session_id]

            audio_queue.put((service_record_id, chunk_number, audio_bytes))

            print(
                f"[INGESTOR] Queued chunk={chunk_number} "
                f"SR={service_record_id} rp={rp_id}"
            )

        except Exception as e:
            print(f"[INGESTOR] MQTT message error: {e}")

    # ===============================
    # AUDIO PROCESSOR THREAD
    # ===============================

    def process_audio_queue():
        while True:
            service_record_id, chunk_number, audio_bytes = audio_queue.get()
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".mp3",
                    prefix="chunk_",
                    delete=False
                ) as tmp:
                    tmp.write(audio_bytes)
                    temp_path = tmp.name

                result = WHISPER_MODEL.transcribe(
                    temp_path,
                    language="id",
                    fp16=(DEVICE == "cuda"),
                    verbose=False
                )

                text = result.get("text", "").strip()

                if not text or len(text) < 3:
                    continue

                session_text_buffer[service_record_id] += " " + text
                full_text = session_text_buffer[service_record_id].strip()

                with app.app_context():
                    record = (
                        db.session.query(ServiceRecord)
                        .filter_by(service_record_id=service_record_id)
                        .first()
                    )

                    # ===== SERVICE DETECTION =====
                    if record and not record.service_detected:
                        if len(full_text.split()) >= 8:
                            key, label, base_conf, keywords = detect_service(full_text)

                            print(
                                "[NLP]",
                                "key=", key,
                                "label=", label,
                                "base_conf=", base_conf,
                                "keywords=", keywords
                            )

                            if key:
                                SESSION_KEYWORD_COUNT[service_record_id] += 1
                                hits = SESSION_KEYWORD_COUNT[service_record_id]

                                confidence = min(1.0, 0.5 + 0.15 * hits)

                                print(
                                    f"[NLP HIT] SR={service_record_id} "
                                    f"hits={hits} confidence={confidence}"
                                )

                                if confidence >= 0.75:
                                    record.service_detected = label
                                    record.service_id = SERVICE_KEY_TO_DB_ID.get(key)
                                    record.confidence = round(confidence, 2)

                                    db.session.commit()
                                    SESSION_KEYWORD_COUNT.pop(service_record_id, None)

                                    print(
                                        f"[SERVICE LOCKED] SR={service_record_id} "
                                        f"{label} ({key}) conf={confidence}"
                                    )

                # ===== SAVE CHUNK =====
                if len(text) > 255:
                    text = text[:255]

                with app.app_context():
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
                        service_record_id=service_record_id,
                        text_chunk=text,
                        created_at=datetime.now(timezone.utc)
                    )

                    db.session.add(chunk)
                    db.session.commit()

                    print(
                        f"[DB] Saved chunk {chunk_id} "
                        f"SR={service_record_id}"
                    )

            except Exception as e:
                print(f"[INGESTOR] Processing error: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                audio_queue.task_done()

    # ===============================
    # START THREADS
    # ===============================

    threading.Thread(
        target=process_audio_queue,
        daemon=True
    ).start()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)

    print("[INGESTOR] MQTT loop started")

    threading.Thread(
        target=client.loop_forever,
        daemon=True
    ).start()
