import os
import time
import json
import base64
import tempfile
from datetime import datetime

from pydub import AudioSegment
from paho.mqtt import client as mqtt_client


# ======================================
# CONFIG (MATCH INGESTOR)
# ======================================

RP_ID = "RP0002"
AUDIO_FILE = "data/audio/pendaftaranmbca_laki_tidakfasih.mp3"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

TOPIC_AUDIO = f"rp/{RP_ID}/audio/stream"
TOPIC_KWS = f"rp/{RP_ID}/event/kws"

CHUNK_MS = 3000
PUBLISH_DELAY = 0.5


# ======================================
# MQTT SETUP
# ======================================

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected rc={rc}")

client = mqtt_client.Client(protocol=mqtt_client.MQTTv311)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

time.sleep(1)  # ensure connection


# ======================================
# KWS START (SESSION BEGIN)
# ======================================

session_hint = datetime.now().strftime("%Y%m%d-%H%M%S")

print("[SIM] Sending KWS MULAI")

client.publish(
    TOPIC_KWS,
    payload=json.dumps({
        "event": "start",
        "session_hint": session_hint
    }),
    qos=1
)

time.sleep(1.5)  # IMPORTANT: give ingestor time to create session


# ======================================
# LOAD & SPLIT AUDIO
# ======================================

audio = AudioSegment.from_file(AUDIO_FILE, format="mp3")
chunks = []

for i in range(0, len(audio), CHUNK_MS):
    chunk = audio[i:i + CHUNK_MS]
    if len(chunk) < 1000:
        chunk += AudioSegment.silent(duration=1000 - len(chunk))
    chunks.append(chunk)

print(f"[SIM] Streaming {len(chunks)} audio chunks")


# ======================================
# STREAM AUDIO
# ======================================

for idx, chunk in enumerate(chunks, start=1):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        chunk.export(tmp.name, format="mp3")
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()

    payload = {
        "chunk_number": idx,
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8")
    }

    client.publish(
        TOPIC_AUDIO,
        payload=json.dumps(payload),
        qos=0
    )

    print(f"[SIM] Published chunk {idx}")

    os.remove(tmp_path)
    time.sleep(PUBLISH_DELAY)


# ======================================
# KWS END (SESSION FINISH)
# ======================================

print("[SIM] Sending KWS SELESAI")

client.publish(
    TOPIC_KWS,
    payload=json.dumps({
        "event": "selesai"
    }),
    qos=1
)

time.sleep(1)

client.loop_stop()
client.disconnect()

print("[SIM] Simulation complete")
