import os
import queue
import tempfile
import threading
import json
import base64
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import whisper
from flask import current_app
from app.extensions import db
from app.models.service_chunk import ServiceChunk
from app.models.service_record import ServiceRecord

# === Audio queue for processing ===
audio_queue = queue.Queue()

# === Session mapping: session_id -> service_record_id ===
active_sessions = {}  # key: session_id, value: service_record_id

# === Load Whisper model once ===
model = whisper.load_model("base")  # "base" or "small", "medium"

def start_ingestor(app, broker="localhost", port=1883):
    """
    MQTT client that ingests audio chunks from RPs, transcribes via Whisper, 
    and saves text chunks into the database.
    """
    topic = "+/audio/stream"

    def on_connect(client, userdata, flags, rc):
        print(f"[INGESTOR] Connected to MQTT broker with code {rc}")
        client.subscribe(topic)
        print(f"[INGESTOR] Subscribed to topic: {topic}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
            audio_bytes = base64.b64decode(payload["audio_base64"])
            rp_id = msg.topic.split("/")[0]  # Extract RP ID from topic
            session_id = payload.get("session_id", rp_id)  # fallback to RP ID if session_id not provided

            # Get or create service_record_id for this session
            with app.app_context():
                if session_id not in active_sessions:
                    last_record = db.session.query(ServiceRecord).order_by(ServiceRecord.service_record_id.desc()).first()
                    new_id = ServiceRecord.generate_id(last_record.service_record_id if last_record else None)

                    service_record = ServiceRecord(
                        service_record_id=new_id,
                        workstation_id=rp_id,
                        start_time=datetime.now(timezone.utc)
                    )
                    db.session.add(service_record)
                    db.session.commit()

                    active_sessions[session_id] = new_id

                service_record_id = active_sessions[session_id]

            chunk_number = payload.get("chunk_number", 0)

            # Queue the chunk for processing
            audio_queue.put((service_record_id, chunk_number, audio_bytes))
            print(f"[INGESTOR] Queued chunk {chunk_number} for {service_record_id} from {rp_id}")

        except Exception as e:
            print(f"[INGESTOR] Failed to process MQTT message: {e}")

    def process_audio_queue():
        while True:
            service_record_id, chunk_number, audio_bytes = audio_queue.get()
            temp_path = None
            try:
                # Write bytes to a temporary WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", prefix="chunk_", delete=False) as tmpfile:
                    tmpfile.write(audio_bytes)
                    temp_path = tmpfile.name

                # Transcribe WAV file with Whisper
                result = model.transcribe(temp_path, language="id")
                text = result.get("text", "").strip()

                # Trim text to 255 characters for DB
                if len(text) > 255:
                    text = text[:255]

                # Save chunk to DB
                with app.app_context():
                    last_chunk = db.session.query(ServiceChunk).order_by(ServiceChunk.chunk_id.desc()).first()
                    chunk_id = ServiceChunk.generate_id(last_chunk.chunk_id if last_chunk else None)

                    new_chunk = ServiceChunk(
                        chunk_id=chunk_id,
                        service_record_id=service_record_id,
                        text_chunk=text,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.session.add(new_chunk)
                    db.session.commit()

                    print(f"[INGESTOR] Saved chunk {chunk_id} for {service_record_id}")

            except Exception as e:
                print(f"[INGESTOR] Failed processing chunk: {e}")

            finally:
                # Cleanup temp file
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                audio_queue.task_done()

    # Start processing thread
    threading.Thread(target=process_audio_queue, daemon=True).start()

    # Start MQTT client in its own thread
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)
    print("[INGESTOR] Starting MQTT loop...")
    threading.Thread(target=client.loop_forever, daemon=True).start()
