# scripts/ingestor_whisper.py
import os
import queue
import tempfile
import threading
import paho.mqtt.client as mqtt
import whisper
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models.service_chunk import ServiceChunk

# === Config ===
MQTT_BROKER = "mqtt_broker_address"
MQTT_PORT = 1883
MQTT_TOPIC = "audio/chunks/#"

app = create_app()
model = whisper.load_model("base")  # You can switch to "small" or "medium"

audio_queue = queue.Queue()

# === MQTT callback ===
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with code", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    # Expect payload to be dict: { "service_record_id": "...", "chunk_number": n, "audio_bytes": b"..." }
    import json, base64
    payload = json.loads(msg.payload)
    audio_bytes = base64.b64decode(payload["audio_bytes"])
    service_record_id = payload["service_record_id"]
    chunk_number = payload["chunk_number"]

    # Put in queue
    audio_queue.put((service_record_id, chunk_number, audio_bytes))
    print(f"Queued chunk {chunk_number} for {service_record_id}")

# === Audio processing thread ===
def process_audio_queue():
    while True:
        service_record_id, chunk_number, audio_bytes = audio_queue.get()
        try:
            # Save temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(audio_bytes)
                temp_path = f.name

            # Transcribe
            result = model.transcribe(temp_path, language="id")
            text = result["text"]

            # Save to DB
            with app.app_context():
                # Generate chunk_id safely
                last_chunk = (
                    ServiceChunk.query
                    .order_by(ServiceChunk.chunk_id.desc())
                    .first()
                )
                last_id = last_chunk.chunk_id if last_chunk else None
                chunk_id = ServiceChunk.generate_id(last_id)

                new_chunk = ServiceChunk(
                    chunk_id=chunk_id,
                    service_record_id=service_record_id,
                    text_chunk=text,
                    created_at=datetime.now(timezone.utc)
                )
                db.session.add(new_chunk)
                db.session.commit()
                print(f"Saved chunk {chunk_id} for {service_record_id}")
        finally:
            # Cleanup
            os.remove(temp_path)
            audio_queue.task_done()

# === Start processing thread ===
threading.Thread(target=process_audio_queue, daemon=True).start()

# === MQTT client ===
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("Starting MQTT loop...")
client.loop_forever()
