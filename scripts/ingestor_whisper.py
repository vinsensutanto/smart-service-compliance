import os
import queue
import tempfile
import threading
import json
import base64
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import whisper

# Will be provided by Flask app later
db = None
ServiceChunk = None

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "+/audio/stream"
AUDIO_QUEUE_MAXSIZE = 20  # prevent GPU overload

# Queue to process audio chunks sequentially
audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAXSIZE)

# Global flags
_ingestor_started = False
model = None

def load_model():
    global model
    if model is None:
        print("[INGESTOR] Loading Whisper model...")
        model = whisper.load_model("base")  # or "small" if GPU limited

def on_connect(client, userdata, flags, rc):
    print(f"[INGESTOR] Connected to MQTT broker with code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"[INGESTOR] Subscribed to topic: {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        audio_bytes = base64.b64decode(payload["audio_base64"])
        session_id = payload["session_id"]
        chunk_number = payload["chunk_number"]

        # Put into queue
        audio_queue.put((session_id, chunk_number, audio_bytes))
        print(f"[INGESTOR] Queued chunk {chunk_number} for {session_id}")

    except Exception as e:
        print(f"[INGESTOR] Failed to queue chunk: {e}")

def process_audio_queue(app):
    global db, ServiceChunk
    load_model()
    while True:
        session_id, chunk_number, audio_bytes = audio_queue.get()
        temp_path = None
        try:
            # Save temp WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", prefix=f"chunk_{chunk_number}_", delete=False) as tmpfile:
                tmpfile.write(audio_bytes)
                temp_path = tmpfile.name

            from pydub import AudioSegment
            audio_seg = AudioSegment.from_file(temp_path, format="wav")
            if len(audio_seg) < 1000:
                audio_seg += AudioSegment.silent(duration=1000 - len(audio_seg))
                audio_seg.export(temp_path, format="wav")

            # Transcribe
            result = model.transcribe(temp_path, language="id")
            text = result.get("text", "").strip()

            with app.app_context():
                from app.extensions import db as db_ext
                from app.models.service_chunk import ServiceChunk as SC
                db = db_ext
                ServiceChunk = SC

                last_chunk = SC.query.order_by(SC.chunk_id.desc()).first()
                last_id = last_chunk.chunk_id if last_chunk else None
                chunk_id = SC.generate_id(last_id)

                new_chunk = SC(
                    chunk_id=chunk_id,
                    service_record_id=session_id,
                    text_chunk=text,
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(new_chunk)
                db.session.commit()
                print(f"[INGESTOR] Saved chunk {chunk_id} for {session_id}")

        except Exception as e:
            print(f"[INGESTOR] Failed processing chunk {chunk_number} for {session_id}: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            audio_queue.task_done()

def start_ingestor(app, broker=MQTT_BROKER, port=MQTT_PORT):
    global _ingestor_started
    if _ingestor_started:
        print("[INGESTOR] Already started, skipping MQTT loop")
        return

    # Start processing thread
    threading.Thread(target=process_audio_queue, args=(app,), daemon=True).start()

    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)
    print("[INGESTOR] Starting MQTT loop...")
    client.loop_start()

    _ingestor_started = True
