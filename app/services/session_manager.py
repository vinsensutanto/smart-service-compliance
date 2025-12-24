from datetime import datetime

# GLOBAL in-memory session registry
active_sessions = {}


class Session:
    def __init__(self, session_id, user_id, workstation_id):
        self.session_id = session_id
        self.user_id = user_id
        self.workstation_id = workstation_id

        self.start_dt = datetime.now()
        self.end_dt = None

        self.text = ""
        self.service_detected = None
        self.confidence = None

        self.checklist = []
        self.audio_chunks = []

    def add_audio(self, chunk):
        if chunk:
            self.audio_chunks.append(chunk)

    def end(self):
        self.end_dt = datetime.now()

    @property
    def duration(self):
        if self.end_dt:
            return int((self.end_dt - self.start_dt).total_seconds())
        return None

    def serialize(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workstation_id": self.workstation_id,
            "start_time": self.start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_time": self.end_dt.strftime("%Y-%m-%d %H:%M") if self.end_dt else None,
            "duration": self.duration,
            "service_detected": self.service_detected,
            "confidence": self.confidence,
            "text": self.text.strip(),
            "checklist": self.checklist,
            "audio_chunks": len(self.audio_chunks),
        }
