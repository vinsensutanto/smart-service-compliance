import os
import threading
from flask import Flask
from dotenv import load_dotenv
from app.config import Config
from app.extensions import db, login_manager, socketio, csrf
from app.models.user import User
from app.services.audio_ingestor import start_ingestor
from app.routes.service import service_bp
from app.routes.sop_page_routes import sop_page_bp
from app.routes.auth import auth_api_bp 
from app.auth.routes import auth_web_bp
from app.cs.routes import cs_bp
from app.spv.routes import spv_bp

def create_app(start_services=False):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        template_folder="templates"
    )
    
    app.config.from_object(Config)
    
    # === Init extensions ===
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    @login_manager.user_loader
    def load_user(user_id):
        # Gunakan session.get() untuk SQLAlchemy versi terbaru
        return db.session.get(User, user_id)

    # === Register routes ===
    # app.register_blueprint(auth_bp)
    app.register_blueprint(auth_api_bp, url_prefix="/api")
    app.register_blueprint(auth_web_bp)
    app.register_blueprint(service_bp, url_prefix="/api")
    app.register_blueprint(sop_page_bp)
    app.register_blueprint(cs_bp, url_prefix='/cs')
    app.register_blueprint(spv_bp, url_prefix='/spv')

    # === START BACKGROUND SERVICES ===
    # Gunakan pengecekan WERKZEUG_RUN_MAIN agar tidak jalan double saat auto-reload
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("[BOOT] Starting Background Services")
        
        # 1. Start Audio Ingestor
        thread_ingestor = threading.Thread(target=start_ingestor, args=(app,))
        thread_ingestor.daemon = True
        thread_ingestor.start()

        # 2. Start MQTT (Jika start_services True)
        if start_services:
            from app.services.mqtt_client import start_mqtt
            thread_mqtt = threading.Thread(target=start_mqtt)
            thread_mqtt.daemon = True
            thread_mqtt.start()
            pass

    return app