from app.extensions import db

class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.String(6), primary_key=True)
    role_name = db.Column(db.String(50), unique=True)
