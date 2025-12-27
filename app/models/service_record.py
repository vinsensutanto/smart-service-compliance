from app.extensions import db


class ServiceRecord(db.Model):
    __tablename__ = "service_records"

    service_record_id = db.Column(db.String(6), primary_key=True)
    workstation_id = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.String(10), nullable=True)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)

    service_detected = db.Column(db.String(100), nullable=True)
    service_id = db.Column(db.String(50), nullable=True)
    confidence = db.Column(db.Float, nullable=True)

    text = db.Column(db.Text, nullable=True)
    audio_path = db.Column(db.String(255), nullable=True)
    is_normal_flow = db.Column(db.Boolean, default=True)
    reason = db.Column(db.String(255)) 

    @staticmethod
    def generate_id(last_id):
        if not last_id:
            return "SR0001"
        num = int(last_id[2:]) + 1
        return f"SR{num:04d}"
