# app/services/ingestor_whisper.py
import os
import queue
import tempfile
import threading
import json
import base64
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pydub import AudioSegment

from app.services.whisper_model import get_whisper_model

# === Config ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "+/audio/stream"
AUDIO_QUEUE_MAXSIZE = 20

audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAXSIZE)
_ingestor_started = False


def on_connect(client, userdata, flags, rc):
    print(f"[INGESTOR] Connected to MQTT broker with code {rc}")
    client.subscribe(MQTT_TOPIC)
    print(f"[INGESTOR] Subscribed to topic: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        session_id = payload["session_id"]
        chunk_number = payload["chunk_number"]
        audio_bytes = base64.b64decode(payload["audio_base64"])

        audio_queue.put((session_id, chunk_number, audio_bytes))
        print(f"[INGESTOR] Queued chunk {chunk_number} for {session_id}")

    except Exception as e:
        print(f"[INGESTOR] Failed to queue chunk: {e}")


def process_audio_queue(app):
    model = get_whisper_model()

    while True:
        session_id, chunk_number, audio_bytes = audio_queue.get()
        temp_path = None

        try:
            # Save temp MP3
            with tempfile.NamedTemporaryFile(
                suffix=".mp3",
                prefix=f"chunk_{chunk_number}_",
                delete=False
            ) as tmpfile:
                tmpfile.write(audio_bytes)
                temp_path = tmpfile.name

            # Ensure minimum duration
            audio = AudioSegment.from_file(temp_path, format="mp3")
            if len(audio) < 1000:
                audio += AudioSegment.silent(duration=1000 - len(audio))
                audio.export(temp_path, format="mp3")

            # Transcribe
            result = model.transcribe(temp_path, language="id")
            text = result.get("text", "").strip()

            with app.app_context():
                from app.extensions import db
                from app.models.service_chunk import ServiceChunk

                last = ServiceChunk.query.order_by(
                    ServiceChunk.chunk_id.desc()
                ).first()

                chunk_id = ServiceChunk.generate_id(
                    last.chunk_id if last else None
                )

                db.session.add(
                    ServiceChunk(
                        chunk_id=chunk_id,
                        service_record_id=session_id,
                        text_chunk=text,
                        created_at=datetime.now(timezone.utc),
                    )
                )
                db.session.commit()

                print(f"[INGESTOR] Saved chunk {chunk_id} for {session_id}")

        except Exception as e:
            print(
                f"[INGESTOR] Failed processing chunk {chunk_number} "
                f"for {session_id}: {e}"
            )

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            audio_queue.task_done()


def start_ingestor(app, broker=MQTT_BROKER, port=MQTT_PORT):
    global _ingestor_started
    if _ingestor_started:
        print("[INGESTOR] Already started, skipping duplicate start")
        return

    threading.Thread(
        target=process_audio_queue,
        args=(app,),
        daemon=True
    ).start()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)

    print("[INGESTOR] Starting MQTT loop...")
    client.loop_start()

    _ingestor_started = True
