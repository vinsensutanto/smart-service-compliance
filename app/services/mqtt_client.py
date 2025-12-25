import json
import paho.mqtt.client as mqtt
from datetime import datetime
import base64
import tempfile
from pydub import AudioSegment

from app.services.session_manager import active_sessions, Session
from app.services.session_store import persist_session
from app.extensions import socketio

flask_app = None


def extract_rp_id(topic):
    """Extract Raspberry Pi ID from topic."""
    return topic.split("/")[0]


def format_timestamp(ts=None):
    """Return formatted timestamp YYYY-MM-DD HH:MM."""
    if ts:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected with result code", rc)
    
    client.subscribe("+/event/kws/start")   # all RP start events
    client.subscribe("+/event/kws/end")     # all RP stop/end events
    client.subscribe("+/audio/stream")      # all RP audio streams



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

        session_id = f"{format_timestamp()}-{rp_id}"

        session = Session(
            session_id=session_id,
            user_id="unknown",        # Will be updated after CS login
            workstation_id=rp_id,
            start_time=format_timestamp()
        )

        active_sessions[rp_id] = session
        print(f"[SESSION START] {session_id}")

        # Tell RP to start streaming
        client.publish(f"/server/control/{rp_id}/start",
                    json.dumps({"command": "start_stream", "session_id": session_id}))

    # -----------------------------
    # AUDIO STREAM
    # -----------------------------
    elif topic.endswith("/audio/stream"):
        session = active_sessions.get(rp_id)
        if not session:
            return

        chunk_b64 = payload.get("audio_base64")
        if chunk_b64:
            # Decode Base64 to bytes
            audio_bytes = base64.b64decode(chunk_b64)

            # Save to a temporary mp3 file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpfile:
                tmpfile.write(audio_bytes)
                temp_path = tmpfile.name

            # Optional: convert to AudioSegment (if needed)
            audio_seg = AudioSegment.from_file(temp_path, format="mp3")

            # Add to session
            session.add_audio(temp_path)  # store file path instead of raw bytes

            # Run STT/NLP inside Flask context safely
            from app import create_app
            from app.extensions import db
            from app.services.nlp_service import classify_service, get_sop_for_service

            app = create_app()
            with app.app_context():
                # Example: classify service based on full session text
                nlp_result = classify_service(session.text, db.session)
                session.service_detected = nlp_result["service_detected"]
                session.confidence = nlp_result["confidence"]

                # Get SOP data
                sop_data = get_sop_for_service(session.service_detected, db.session)
                session.checklist = sop_data

            # Emit live updates to Web UI
            from app.extensions import socketio
            socketio.emit("session_text", {
                "session_id": session.session_id,
                "text": session.text
            })
            socketio.emit("sop_update", {
                "session_id": session.session_id,
                "service": session.service_detected,
                "sop": sop_data
            })

            print(f"[AUDIO] {rp_id} | session={session.session_id} | chunks={len(session.audio_chunks)}")

    # -----------------------------
    # SESSION STOP
    # -----------------------------
    elif topic.endswith("/event/kws/stop"):
        session = active_sessions.pop(rp_id, None)
        if not session:
            return

        session.end()
        print(f"[SESSION END] {session.session_id} | duration={session.duration_sec}s")

        # Update UI
        socketio.emit("session_end", session.serialize())

        # Persist to DB
        with flask_app.app_context():
            session.persist_to_db()

        # Tell RP to stop streaming
        client.publish(f"/server/control/{rp_id}/end",
                    json.dumps({"command": "stop_stream", "session_id": session.session_id}))

def start_mqtt(app):
    """Start MQTT client in Flask app context."""
    global flask_app
    flask_app = app

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(app.config["MQTT_BROKER"], app.config["MQTT_PORT"], 60)
    client.loop_start()
