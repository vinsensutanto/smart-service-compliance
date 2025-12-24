# app/services/session_manager.py
from datetime import datetime
from scripts.stt_whisper import transcribe_chunk
from app.extensions import db
from app.models.service_chunk import ServiceChunk
from sqlalchemy import func, cast, Integer

# In-memory session registry
active_sessions = {}

class Session:
    def __init__(self, session_id, user_id, workstation_id):
        self.session_id = session_id
        self.user_id = user_id
        self.workstation_id = workstation_id

        self.start_time = datetime.now()
        self.end_time = None

        self.text = ""
        self.service_detected = None
        self.confidence = None

        self.checklist = []
        self.audio_chunks = []

    def add_audio(self, chunk):
        """Add chunk and run STT immediately."""
        if chunk:
            self.audio_chunks.append(chunk)
            self.process_stt(chunk)

    def process_stt(self, chunk):
        """Incrementally process audio chunk to text using Whisper."""
        try:
            text = transcribe_chunk(chunk)
            if text:
                self.text += " " + text
        except Exception as e:
            print(f"[STT ERROR] {self.session_id}: {e}")

    def end(self):
        self.end_time = datetime.now()

    @property
    def duration_sec(self):
        if not self.end_time:
            return 0
        return int((self.end_time - self.start_time).total_seconds())

    def serialize(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workstation_id": self.workstation_id,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M") if self.end_time else None,
            "duration": self.duration_sec,
            "service_detected": self.service_detected,
            "confidence": self.confidence,
            "text": self.text.strip(),
            "checklist": self.checklist,
            "audio_chunks": len(self.audio_chunks),
        }

    def persist_to_db(self):
        """Save session text into service_chunks table."""
        if not self.text.strip():
            return

        try:
            # Get last numeric chunk_id
            last_chunk = (
                ServiceChunk.query
                .order_by(cast(func.substr(ServiceChunk.chunk_id, 3), Integer).desc())
                .first()
            )
            last_id = last_chunk.chunk_id if last_chunk else None

            # Split text into chunks of 255 characters
            chunks = [self.text[i:i+255] for i in range(0, len(self.text), 255)]

            for chunk_text in chunks:
                chunk_id = ServiceChunk.generate_id(last_id)
                last_id = chunk_id

                new_chunk = ServiceChunk(
                    chunk_id=chunk_id,
                    service_record_id=self.session_id,
                    text_chunk=chunk_text,
                    created_at=datetime.now()
                )
                db.session.add(new_chunk)

            db.session.commit()
            print(f"[DB] Saved {len(chunks)} chunk(s) for session {self.session_id}")

        except Exception as e:
            db.session.rollback()
            print(f"[DB ERROR] Failed to save session {self.session_id}: {e}")
