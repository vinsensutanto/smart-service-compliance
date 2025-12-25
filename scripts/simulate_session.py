import os
import time
import json
import base64
import tempfile
from datetime import datetime
from pydub import AudioSegment
from paho.mqtt import client as mqtt_client

# --- Simulation Config ---
rp_id = "WS0001"
session_id = f"{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}-{rp_id}"
audio_file = "data/audio/pendaftaranmbca_laki_tidakfasih.mp3"
chunk_length_ms = 3000
mqtt_broker = "localhost"
mqtt_port = 1883
topic = f"{rp_id}/audio/stream"

print(f"[SIMULATION] Session started: {session_id}")

# --- Load audio and split into chunks ---
audio = AudioSegment.from_file(audio_file, format="mp3")
chunks = []
for i in range(0, len(audio), chunk_length_ms):
    chunk = audio[i:i + chunk_length_ms]
    if len(chunk) < 1000:
        chunk += AudioSegment.silent(duration=1000 - len(chunk))
    chunks.append(chunk)

# --- MQTT Setup ---
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")

client = mqtt_client.Client(protocol=mqtt_client.MQTTv311)
client.on_connect = on_connect
client.connect(mqtt_broker, mqtt_port, 60)
client.loop_start()

# --- Publish chunks to MQTT only ---
for i, chunk in enumerate(chunks, start=1):
    with tempfile.NamedTemporaryFile(suffix=".mp3", prefix=f"chunk_{i}_", delete=False) as tmpfile:
        chunk.export(tmpfile.name, format="mp3")
        temp_path = tmpfile.name

    with open(temp_path, "rb") as f:
        audio_bytes = f.read()

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "session_id": session_id,
        "chunk_number": i,
        "audio_base64": audio_b64
    }

    client.publish(topic, json.dumps(payload))
    print(f"[CHUNK {i}] Published to MQTT")
    os.remove(temp_path)
    time.sleep(0.5)

print(f"[SIMULATION] Session ended (MQTT only)")

client.loop_stop()
client.disconnect()
