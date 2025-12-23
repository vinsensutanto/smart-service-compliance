from app.extensions import db
from sqlalchemy import CheckConstraint

class SOPStep(db.Model):
    __tablename__ = "sop_steps"

    step_id = db.Column(db.String(6), primary_key=True)
    service_id = db.Column(
        db.String(6),
        db.ForeignKey("sop_services.service_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    step_number = db.Column(db.Integer)
    step_description = db.Column(db.String(255))

    __table_args__ = (
        CheckConstraint("step_id REGEXP '^ST[0-9]{4}$'", name="chk_step_id"),
    )
