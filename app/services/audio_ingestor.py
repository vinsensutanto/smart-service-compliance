import os
import queue
import tempfile
import threading
import json
import base64
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import whisper
import torch

from flask import current_app
from app.extensions import db
from app.models.service_chunk import ServiceChunk
from app.models.service_record import ServiceRecord

# ===============================
# Whisper / Torch configuration
# ===============================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

print(f"[WHISPER] Using device={DEVICE}, dtype={DTYPE}")

# Load Whisper ONCE
WHISPER_MODEL = whisper.load_model(
    "base",
    device=DEVICE
)

# ===============================
# Audio queue
# ===============================
audio_queue = queue.Queue()

# session_id -> service_record_id
active_sessions = {}

# Prevent double startup
_ingestor_started = False


def start_ingestor(app, broker="localhost", port=1883):
    global _ingestor_started
    if _ingestor_started:
        print("[INGESTOR] Already started, skipping duplicate start")
        return
    _ingestor_started = True

    """
    MQTT client that:
    - receives audio chunks
    - transcribes using Whisper
    - stores text chunks into DB
    """

    topic = "+/audio/stream"

    # ===============================
    # MQTT callbacks
    # ===============================
    def on_connect(client, userdata, flags, rc):
        print(f"[INGESTOR] Connected to MQTT broker with code {rc}")
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
                    last_record = (
                        db.session.query(ServiceRecord)
                        .order_by(ServiceRecord.service_record_id.desc())
                        .first()
                    )

                    new_id = ServiceRecord.generate_id(
                        last_record.service_record_id if last_record else None
                    )

                    service_record = ServiceRecord(
                        service_record_id=new_id,
                        workstation_id=rp_id,
                        start_time=datetime.now(timezone.utc)
                    )
                    db.session.add(service_record)
                    db.session.commit()

                    active_sessions[session_id] = new_id

                service_record_id = active_sessions[session_id]

            audio_queue.put(
                (service_record_id, chunk_number, audio_bytes)
            )

            print(
                f"[INGESTOR] Queued chunk {chunk_number} "
                f"for {service_record_id} from {rp_id}"
            )

        except Exception as e:
            print(f"[INGESTOR] Failed to process MQTT message: {e}")

    # ===============================
    # Audio processing worker
    # ===============================
    def process_audio_queue():
        while True:
            service_record_id, chunk_number, audio_bytes = audio_queue.get()
            temp_path = None

            try:
                # Write chunk to temp WAV
                with tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    prefix="chunk_",
                    delete=False
                ) as tmpfile:
                    tmpfile.write(audio_bytes)
                    temp_path = tmpfile.name

                # Whisper transcription
                result = WHISPER_MODEL.transcribe(
                    temp_path,
                    language="id",
                    fp16=(DEVICE == "cuda"),
                    verbose=False
                )

                text = result.get("text", "").strip()

                # Skip empty / noise chunks safely
                if not text or len(text) < 3:
                    continue

                if len(text) > 255:
                    text = text[:255]

                # Save to DB
                with app.app_context():
                    last_chunk = (
                        db.session.query(ServiceChunk)
                        .order_by(ServiceChunk.chunk_id.desc())
                        .first()
                    )

                    chunk_id = ServiceChunk.generate_id(
                        last_chunk.chunk_id if last_chunk else None
                    )

                    new_chunk = ServiceChunk(
                        chunk_id=chunk_id,
                        service_record_id=service_record_id,
                        text_chunk=text,
                        created_at=datetime.now(timezone.utc)
                    )

                    db.session.add(new_chunk)
                    db.session.commit()

                    print(
                        f"[INGESTOR] Saved chunk {chunk_id} "
                        f"for {service_record_id}"
                    )

            except Exception as e:
                print(f"[INGESTOR] Failed processing chunk: {e}")

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                audio_queue.task_done()

    # ===============================
    # Start worker + MQTT
    # ===============================
    threading.Thread(
        target=process_audio_queue,
        daemon=True
    ).start()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)

    print("[INGESTOR] Starting MQTT loop...")
    threading.Thread(
        target=client.loop_forever,
        daemon=True
    ).start()
