from app.extensions import db
from datetime import datetime

class CSSessionText(db.Model):
    __tablename__ = "cs_session_text"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(6), nullable=False)
    workstation_id = db.Column(db.String(6), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
