# app/services/session_manager.py
from datetime import datetime
from scripts.stt_whisper import transcribe_chunk
from app.extensions import db
from app.models.service_record import ServiceRecord

# In-memory session registry
active_sessions = {}


class Session:
    def __init__(self, session_id, user_id, workstation_id):
        self.session_id = session_id
        self.user_id = user_id
        self.workstation_id = workstation_id

        self.start_time = datetime.utcnow()
        self.end_time = None

        self.audio_chunks = []     # raw audio or paths
        self.text = ""             # full transcript
        self.text_chunks = []      # optional per-chunk text
        self.checklist = []

        self.service_detected = None
        self.confidence = 0.0

        # 🔑 Create DB record immediately
        self.service_record_id = self._create_service_record()

    def _create_service_record(self):
        last = (
            ServiceRecord.query
            .order_by(ServiceRecord.service_record_id.desc())
            .first()
        )

        new_id = ServiceRecord.generate_id(
            last.service_record_id if last else None
        )

        record = ServiceRecord(
            service_record_id=new_id,
            workstation_id=self.workstation_id,
            user_id=self.user_id,
            start_time=self.start_time
        )

        db.session.add(record)
        db.session.commit()

        return new_id

    def add_audio_chunk(self, chunk):
        """Store chunk + run STT"""
        if not chunk:
            return

        self.audio_chunks.append(chunk)

        try:
            text = transcribe_chunk(chunk)
            if text:
                self.text += " " + text
                self.text_chunks.append(text)
        except Exception as e:
            print(f"[STT ERROR] {self.session_id}: {e}")

    def end(self):
        self.end_time = datetime.utcnow()

    @property
    def duration_sec(self):
        if not self.end_time:
            return None
        return int((self.end_time - self.start_time).total_seconds())

    def serialize(self):
        return {
            "session_id": self.session_id,
            "service_record_id": self.service_record_id,
            "user_id": self.user_id,
            "workstation_id": self.workstation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration_sec,
            "service_detected": self.service_detected,
            "confidence": self.confidence,
            "text": self.text.strip(),
            "checklist": self.checklist,
            "audio_chunks": len(self.audio_chunks),
        }
