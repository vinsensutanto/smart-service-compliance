import os
from flask import Flask
from dotenv import load_dotenv
from app.config import Config
from app.extensions import db, login_manager, socketio, csrf
from app.models.user import User

from app.services.audio_ingestor import start_ingestor

from app.routes.service import service_bp
from app.routes.auth import auth_bp
from app.routes.sop_page_routes import sop_page_bp



def create_app(start_services=False):
    
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        template_folder="templates"
    )
    
    app.config.from_object(Config)
    app.config['DEBUG'] = True  # aktifkan debug
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # reload template otomatis

    # === Init extensions ===
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # socketio.init_app(app, cors_allowed_origins="*")
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # === Register routes ===
    app.register_blueprint(auth_bp)
    app.register_blueprint(service_bp, url_prefix="/api")
    app.register_blueprint(sop_page_bp)

    # === START AUDIO INGESTOR ONLY ===
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("[BOOT] Starting Audio Ingestor")
        with app.app_context():
            start_ingestor(app)

    if start_services:
        from app.services.audio_ingestor import start_ingestor
        from app.services.mqtt_client import start_mqtt
        start_ingestor()
        start_mqtt()

    return app
