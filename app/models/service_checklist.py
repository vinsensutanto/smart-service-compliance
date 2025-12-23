from app.extensions import db

class ServiceChecklist(db.Model):
    __tablename__ = "service_checklists"

    checklist_id = db.Column(db.String(6), primary_key=True)
    service_record_id = db.Column(db.String(6), db.ForeignKey("service_records.service_record_id"))
    step_id = db.Column(db.String(6), db.ForeignKey("sop_steps.step_id"))

    is_checked = db.Column(db.Boolean, default=False)
    checked_at = db.Column(db.DateTime)
