from app.extensions import db

class SOPStep(db.Model):
    __tablename__ = "sop_steps"

    step_id = db.Column(db.String(6), primary_key=True)
    service_id = db.Column(db.String(6), db.ForeignKey("sop_services.service_id"))
    step_number = db.Column(db.Integer)
    step_description = db.Column(db.String(255))
