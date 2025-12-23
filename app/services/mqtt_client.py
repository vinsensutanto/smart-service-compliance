import json
import paho.mqtt.client as mqtt
from datetime import datetime

from app.services.session_manager import active_sessions, Session
from app.services.session_store import persist_session
from app.extensions import socketio

BROKER = "localhost"
PORT = 1883


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

    # --- SESSION START ---
    if topic.endswith("/event/kws/start"):
        session_id = f"{datetime.now().strftime('%Y-%m-%d-%H:%M')}-{rp_id}"

        session = Session(
            session_id=session_id,
            user_id="unknown",
            workstation_id=rp_id
        )

        active_sessions[rp_id] = session
        print(f"[SESSION START] {session_id}")

    # --- AUDIO STREAM ---
    elif topic.endswith("/audio/stream"):
        session = active_sessions.get(rp_id)
        if not session:
            return

        chunk = payload.get("chunk")
        session.add_audio(chunk)

        print(
            f"[AUDIO] {rp_id} | "
            f"session={session.session_id} | "
            f"chunks={len(session.audio_chunks)}"
        )

    # --- SESSION STOP ---
    elif topic.endswith("/event/kws/stop"):
        session = active_sessions.pop(rp_id, None)

        if not session:
            print(f"[WARN] Stop without session ({rp_id})")
            return

        session.end()

        print(f"[SESSION END] {session.session_id}")

        # UI update
        socketio.emit("session_end", session.serialize())

        # Persistence (Step 5.3)
        persist_session(session)


def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()
