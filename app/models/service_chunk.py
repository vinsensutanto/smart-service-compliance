from app.extensions import db

class ServiceChunk(db.Model):
    __tablename__ = "service_chunks"

    chunk_id = db.Column(db.String(6), primary_key=True)
    service_record_id = db.Column(db.String(6), db.ForeignKey("service_records.service_record_id"))
    text_chunk = db.Column(db.Text)
