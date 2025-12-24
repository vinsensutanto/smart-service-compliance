import os
import time
import json
import base64
import tempfile
from datetime import datetime
from pydub import AudioSegment
from paho.mqtt import client as mqtt_client

from app import create_app
from app.services.session_manager import active_sessions, Session
from app.services.session_store import persist_session

# --- Setup Flask App ---
app = create_app()

# --- Session Setup ---
rp_id = "WS0001"
session_id = f"{datetime.now().strftime('%Y-%m-%d-%H:%M')}-{rp_id}"
session = Session(session_id=session_id, user_id="US0001", workstation_id=rp_id)
active_sessions[rp_id] = session

print(f"[SIMULATION] Session started: {session_id}")

# --- Ensure audio chunk folder exists ---
os.makedirs("data/audio_chunks", exist_ok=True)

# --- Load WAV audio ---
audio_file = "data/audio/pendaftaranmbca_laki_tidakfasih.wav"
audio = AudioSegment.from_file(audio_file, format="wav")

# Split into 3-second chunks
chunk_length_ms = 3000
chunks = []
for i in range(0, len(audio), chunk_length_ms):
    chunk = audio[i:i + chunk_length_ms]
    # Pad last chunk if <1s
    if len(chunk) < 1000:
        silence = AudioSegment.silent(duration=1000 - len(chunk))
        chunk += silence
    chunks.append(chunk)

# --- MQTT Setup ---
mqtt_broker = "localhost"
mqtt_port = 1883
topic = f"{rp_id}/audio/stream"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")

client = mqtt_client.Client(protocol=mqtt_client.MQTTv311)
client.on_connect = on_connect
client.connect(mqtt_broker, mqtt_port, 60)
client.loop_start()

# --- Publish chunks ---
for i, chunk in enumerate(chunks, start=1):
    # Export chunk to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", prefix=f"chunk_{i}_", delete=False) as tmpfile:
        chunk.export(tmpfile.name, format="wav")
        temp_path = tmpfile.name

    # Read bytes
    with open(temp_path, "rb") as f:
        audio_bytes = f.read()

    # Encode Base64
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "session_id": session_id,
        "chunk_number": i,
        "audio_base64": audio_b64
    }

    # Publish once
    client.publish(topic, json.dumps(payload))
    print(f"[CHUNK {i}] Published to MQTT")

    # Simulated local text
    simulated_text = f"[Simulated STT chunk {i}]"
    session.text += " " + simulated_text
    session.audio_chunks.append(simulated_text)
    print(f"[CHUNK {i}] {simulated_text}")

    os.remove(temp_path)
    time.sleep(0.5)  # Simulate real-time streaming

# --- End session ---
session.end()
print(f"[SIMULATION] Session ended: duration={session.duration_sec}s")

# --- Persist session ---
with app.app_context():
    persist_session(session)

print("[SIMULATION] Session persisted to DB")

# Stop MQTT loop
client.loop_stop()
client.disconnect()