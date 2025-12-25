import os
from flask import Flask

from app.config import Config
from app.extensions import db, login_manager, socketio
from app.models.user import User
from app.services.audio_ingestor import start_ingestor
from app.services.mqtt_client import start_mqtt
from app.routes.service import service_bp
from app.routes.auth import auth_bp
from app.routes.sop_page_routes import sop_page_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # === Init extensions ===
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # === Register routes ===
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(service_bp, url_prefix="/api")
    app.register_blueprint(sop_page_bp)

    # === START BACKGROUND SERVICES (SAFE) ===
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("[BOOT] Starting MQTT & Audio Ingestor")

        with app.app_context():
            start_mqtt(app)
            start_ingestor(app)

    return app
