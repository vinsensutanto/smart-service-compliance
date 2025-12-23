from app.extensions import db

class SOPService(db.Model):
    __tablename__ = "sop_services"

    service_id = db.Column(db.String(6), primary_key=True)
    service_name = db.Column(db.String(255))
