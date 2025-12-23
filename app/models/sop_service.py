from app.extensions import db
from sqlalchemy import CheckConstraint

class SOPService(db.Model):
    __tablename__ = "sop_services"

    service_id = db.Column(db.String(6), primary_key=True)
    service_name = db.Column(db.String(255))

    __table_args__ = (
        CheckConstraint("service_id REGEXP '^SV[0-9]{4}$'", name="chk_service_id"),
    )
