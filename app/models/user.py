from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(6), primary_key=True)
    role_id = db.Column(
        db.String(6),
        db.ForeignKey("roles.role_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    email_verified_at = db.Column(db.DateTime, nullable=True)
    password = db.Column(db.String(255))
    remember_token = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("user_id REGEXP '^US[0-9]{4}$'", name="chk_user_id"),
    )

    def get_id(self):
        return self.user_id

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
