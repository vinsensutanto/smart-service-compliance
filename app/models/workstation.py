from app.extensions import db
from sqlalchemy import CheckConstraint

class Workstation(db.Model):
    __tablename__ = "workstations"

    workstation_id = db.Column(db.String(6), primary_key=True)
    pc_id = db.Column(db.String(6))
    rpi_id = db.Column(db.String(6))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)

    __table_args__ = (
        CheckConstraint("workstation_id REGEXP '^WS[0-9]{4}$'", name="chk_workstation_id"),
        CheckConstraint("pc_id REGEXP '^PC[0-9]{4}$'", name="chk_pc_id"),
        CheckConstraint("rpi_id REGEXP '^RP[0-9]{4}$'", name="chk_rpi_id"),
    )
