from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, socketio
from app.models.user import User
from app.services.mqtt_client import start_mqtt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    from app.routes.auth import auth_bp
    from app.routes.service import service_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(service_bp)

    start_mqtt()

    return app
