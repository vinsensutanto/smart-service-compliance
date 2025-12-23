from app.extensions import db
from sqlalchemy import CheckConstraint

class ServiceChunk(db.Model):
    __tablename__ = "service_chunks"

    chunk_id = db.Column(db.String(6), primary_key=True)
    service_record_id = db.Column(
        db.String(6),
        db.ForeignKey("service_records.service_record_id", onupdate="CASCADE", ondelete="CASCADE")
    )
    text_chunk = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("chunk_id REGEXP '^CU[0-9]{4}$'", name="chk_chunk_id"),
    )
