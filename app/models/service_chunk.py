from app.extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime
import uuid

class ServiceChunk(db.Model):
    __tablename__ = "service_chunks"

    chunk_id = db.Column(db.String(6), primary_key=True)
    service_record_id = db.Column(
        db.String(6),
        db.ForeignKey("service_records.service_record_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )
    text_chunk = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("chunk_id REGEXP '^CU[0-9]{4}$'", name="chk_chunk_id"),
    )

    @staticmethod
    def generate_id(last_id=None):
        """
        Generate a numeric chunk_id following CU0001, CU0002, etc.
        Optionally pass last_id to increment.
        """
        if last_id:
            num = int(last_id[2:]) + 1
        else:
            num = 1
        return f"CU{num:04d}"
