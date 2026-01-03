import os
import time
import json
import base64
import tempfile
from datetime import datetime, timezone

from pydub import AudioSegment
from paho.mqtt import client as mqtt_client

# ======================================
# CONFIG (FINAL CONTRACT)
# ======================================

RP_ID = "RP0002"
AUDIO_FILE = "data/audio/penggantiankartuatm_laki_cepat.mp3"
# AUDIO_FILE = "data/audio/pendaftaranmbca_laki_tidakfasih.mp3"
# AUDIO_FILE = "data/audio/pembukaanrekeningtahapan_wanita.mp3"

MQTT_BROKER = "10.159.121.208"
MQTT_PORT = 1883

TOPIC_KWS_START = f"rp/{RP_ID}/event/kws/start"
TOPIC_KWS_END   = f"rp/{RP_ID}/event/kws/end"
TOPIC_AUDIO     = f"rp/{RP_ID}/audio/stream"

CHUNK_MS = 3000
PUBLISH_DELAY = 0.5

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected rc={rc}")

client = mqtt_client.Client(protocol=mqtt_client.MQTTv311)
client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

time.sleep(1)

audio = AudioSegment.from_file(AUDIO_FILE, format="mp3")
chunks = []

for i in range(0, len(audio), CHUNK_MS):
    chunk = audio[i:i + CHUNK_MS]
    if len(chunk) < 1000:
        chunk += AudioSegment.silent(duration=1000 - len(chunk))
    chunks.append(chunk)

print(f"[SIM] Prepared {len(chunks)} audio chunks")

print("[SIM] Sending KWS START")

first_chunk = chunks[0]

with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
    first_chunk.export(tmp.name, format="mp3")
    tmp_path = tmp.name

with open(tmp_path, "rb") as f:
    audio_bytes = f.read()

os.remove(tmp_path)

client.publish(
    TOPIC_KWS_START,
    payload=json.dumps({
        "rp_id": RP_ID,
        "chunk_number": 1,
        "audio": base64.b64encode(audio_bytes).decode(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }),
    qos=1
)

time.sleep(1)

for idx, chunk in enumerate(chunks[1:], start=2):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        chunk.export(tmp.name, format="mp3")
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()

    os.remove(tmp_path)

    payload = {
        "rp_id": RP_ID,
        "chunk_number": idx,
        "audio": base64.b64encode(audio_bytes).decode(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    client.publish(
        TOPIC_AUDIO,
        payload=json.dumps(payload),
        qos=0
    )

    print(f"[SIM] Published chunk {idx}")
    time.sleep(PUBLISH_DELAY)

print("[SIM] Sending KWS END")

client.publish(
    TOPIC_KWS_END,
    payload=json.dumps({
        "rp_id": RP_ID,
        "chunk_number": len(chunks),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }),
    qos=1
)

time.sleep(1)

client.loop_stop()
client.disconnect()

print("[SIM] Simulation complete")
