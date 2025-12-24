from app import create_app
from app.extensions import db
from app.services.audio_ingestor import start_ingestor
from app.services.mqtt_client import start_mqtt

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.engine.connect()
        print("DB connected")

        # Start background services ONCE
        start_mqtt(app)
        start_ingestor(
            app,
            app.config["MQTT_BROKER"],
            app.config["MQTT_PORT"]
        )

    app.run(debug=True, use_reloader=False)