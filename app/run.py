# app/run.py
from app import create_app
from app.extensions import db, socketio
from app.services.audio_ingestor import start_ingestor
from app.services.mqtt_client import start_mqtt

def main():
    app = create_app()

    with app.app_context():
        db.engine.connect()
        print("DB connected")

        start_mqtt(app)
        start_ingestor(
            app,
            app.config["MQTT_BROKER"],
            app.config["MQTT_PORT"]
        )

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )

if __name__ == "__main__":
    main()
