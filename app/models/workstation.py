from app.extensions import db

class Workstation(db.Model):
    __tablename__ = "workstations"

    workstation_id = db.Column(db.String(6), primary_key=True)
    pc_id = db.Column(db.String(6))
    rpi_id = db.Column(db.String(6))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
