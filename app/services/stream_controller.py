# app/services/stream_controller.py
import json
from datetime import datetime, timezone
import paho.mqtt.publish as publish

MQTT_BROKER = "10.159.121.208"
MQTT_PORT = 1883


def publish_end_stream(rp_id: str):
    topic = f"server/control/{rp_id}/end"

    payload = {
        "command": "end",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    }

    publish.single(
        topic,
        payload=json.dumps(payload),
        qos=1,
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )

    print(f"[STREAM] end command sent to RP={rp_id}")
