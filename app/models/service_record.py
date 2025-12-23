from app.extensions import db
from sqlalchemy import CheckConstraint

class ServiceRecord(db.Model):
    __tablename__ = "service_records"

    service_record_id = db.Column(db.String(6), primary_key=True)
    workstation_id = db.Column(
        db.String(6),
        db.ForeignKey("workstations.workstation_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.String(6),
        db.ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE")
    )

    service_detected = db.Column(db.String(255))
    confidence = db.Column(db.Float(precision=2))
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer)
    text = db.Column(db.Text)

    is_normal_flow = db.Column(db.Boolean, default=True)
    reason = db.Column(db.String(255))
    audio_path = db.Column(db.String(255))

    __table_args__ = (
        CheckConstraint("service_record_id REGEXP '^SR[0-9]{4}$'", name="chk_service_record_id"),
    )
