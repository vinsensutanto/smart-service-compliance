# import json
# import paho.mqtt.client as mqtt
# from datetime import datetime
# import base64
# import tempfile
# from pydub import AudioSegment

# from app.services.session_manager import active_sessions, Session
# from app.services.session_store import persist_session
# from app.extensions import socketio

# flask_app = None


# def extract_rp_id(topic):
#     """Extract Raspberry Pi ID from topic."""
#     return topic.split("/")[0]


# def format_timestamp(ts=None):
#     """Return formatted timestamp YYYY-MM-DD HH:MM."""
#     if ts:
#         return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
#     return datetime.now().strftime("%Y-%m-%d %H:%M")


# def on_connect(client, userdata, flags, rc):
#     print("[MQTT] Connected with result code", rc)
    
#     client.subscribe("+/event/kws/start")   # all RP start events
#     client.subscribe("+/event/kws/end")     # all RP stop/end events
#     client.subscribe("+/audio/stream")      # all RP audio streams



# def on_message(client, userdata, msg):
#     topic = msg.topic
#     payload = json.loads(msg.payload.decode())
#     rp_id = extract_rp_id(topic)

#     # -----------------------------
#     # SESSION START
#     # -----------------------------
#     if topic.endswith("/event/kws/start"):
#         session_id = f"{format_timestamp()}-{rp_id}"

#         print(f"[SESSION START] {session_id}")

#         client.publish(
#             f"/server/control/{rp_id}/start",
#             json.dumps({"command": "start_stream", "session_id": session_id})
#         )
    
#     elif topic.endswith("/event/kws/stop"):
#         print(f"[SESSION END] RP={rp_id}")

#         client.publish(
#             f"/server/control/{rp_id}/end",
#             json.dumps({"command": "stop_stream"})
#         )

# def start_mqtt(app):
#     """Start MQTT client in Flask app context."""
#     global flask_app
#     flask_app = app

#     client = mqtt.Client()
#     client.on_connect = on_connect
#     client.on_message = on_message

#     client.connect(app.config["MQTT_BROKER"], app.config["MQTT_PORT"], 60)
#     client.loop_start()
