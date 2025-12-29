import json
import paho.mqtt.publish as publish

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

STREAM_COMMAND_TOPIC = "stream/command"


def publish_end_stream(session_id: str):
    payload = {
        "command": "end_stream",
        "session_id": session_id
    }

    publish.single(
        STREAM_COMMAND_TOPIC,
        payload=json.dumps(payload),
        qos=1,
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )

    print(f"[STREAM] end_stream published for session {session_id}")
