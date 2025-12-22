from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(6), primary_key=True)
    role_id = db.Column(db.String(6), db.ForeignKey("roles.role_id"))
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    def get_id(self):
        return self.user_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
