import json
import paho.mqtt.client as mqtt
from datetime import datetime

from app.services.session_manager import active_sessions, Session
from app.services.session_store import persist_session
from app.extensions import socketio

# ✅ store Flask app reference for threads
flask_app = None


def extract_rp_id(topic):
    return topic.split("/")[0]


def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    client.subscribe("+/event/kws/start")
    client.subscribe("+/event/kws/stop")
    client.subscribe("+/audio/stream")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = json.loads(msg.payload.decode())
    rp_id = extract_rp_id(topic)

    # -----------------------------
    # SESSION START
    # -----------------------------
    if topic.endswith("/event/kws/start"):
        if rp_id in active_sessions:
            print(f"[WARN] Session already active for {rp_id}")
            return

        session_id = f"{datetime.now().strftime('%Y-%m-%d-%H:%M')}-{rp_id}"

        session = Session(
            session_id=session_id,
            user_id="unknown",
            workstation_id=rp_id
        )

        active_sessions[rp_id] = session
        print(f"[SESSION START] {session_id}")

    # -----------------------------
    # AUDIO STREAM
    # -----------------------------
    elif topic.endswith("/audio/stream"):
        session = active_sessions.get(rp_id)
        if not session:
            return

        chunk = payload.get("chunk")
        if chunk:
            session.add_audio(chunk)
            print(
                f"[AUDIO] {rp_id} | "
                f"session={session.session_id} | "
                f"chunks={len(session.audio_chunks)}"
            )

    # -----------------------------
    # SESSION STOP
    # -----------------------------
    elif topic.endswith("/event/kws/stop"):
        session = active_sessions.pop(rp_id, None)
        if not session:
            return

        session.end()
        print(f"[SESSION END] {session.session_id}")

        # WebSocket UI update
        socketio.emit("session_end", session.serialize())

        # ✅ PUSH APP CONTEXT FOR DB
        with flask_app.app_context():
            persist_session(session)


def start_mqtt(app):
    global flask_app
    flask_app = app

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(
        app.config["MQTT_BROKER"],
        app.config["MQTT_PORT"],
        60
    )
    client.loop_start()