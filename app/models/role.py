from app.extensions import db
from sqlalchemy import CheckConstraint

class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.String(6), primary_key=True)
    role_name = db.Column(db.String(100))

    __table_args__ = (
        CheckConstraint("role_id REGEXP '^RL[0-9]{4}$'", name="chk_role_id"),
    )
