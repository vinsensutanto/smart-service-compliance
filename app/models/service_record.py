from app.extensions import db

class ServiceRecord(db.Model):
    __tablename__ = "service_records"

    service_record_id = db.Column(db.String(6), primary_key=True)
    workstation_id = db.Column(db.String(6), db.ForeignKey("workstations.workstation_id"))
    user_id = db.Column(db.String(6), db.ForeignKey("users.user_id"))

    service_detected = db.Column(db.String(255))
    confidence = db.Column(db.Numeric(4,3))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    text = db.Column(db.Text)

    is_normal_flow = db.Column(db.Boolean)
    reason = db.Column(db.String(255))
    audio_path = db.Column(db.String(255))
