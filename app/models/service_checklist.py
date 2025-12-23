from app.extensions import db
from sqlalchemy import CheckConstraint

class ServiceChecklist(db.Model):
    __tablename__ = "service_checklists"

    checklist_id = db.Column(db.String(6), primary_key=True)
    service_record_id = db.Column(
        db.String(6),
        db.ForeignKey("service_records.service_record_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    step_id = db.Column(
        db.String(6),
        db.ForeignKey("sop_steps.step_id", onupdate="CASCADE", ondelete="CASCADE")
    )

    is_checked = db.Column(db.Boolean, default=False)
    checked_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("checklist_id REGEXP '^CE[0-9]{4}$'", name="chk_checklist_id"),
    )
