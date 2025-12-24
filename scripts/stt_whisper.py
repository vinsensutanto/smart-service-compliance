# scripts/stt_whisper.py
import whisper
import sounddevice as sd
import numpy as np
from datetime import datetime, timezone
from app import create_app
from app.extensions import db
from app.models.service_chunk import ServiceChunk
from sqlalchemy import func, cast, Integer

app = create_app()
model = whisper.load_model("base")  # "small", "medium" also possible

def record_audio(duration=5, fs=16000):
    """Record audio from microphone"""
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    return np.squeeze(audio)

def transcribe(audio_file, language="id"):
    """Transcribe audio file using Whisper"""
    result = model.transcribe(audio_file, language=language)
    return result["text"]

def save_chunks(service_record_id, text, chunk_size=255):
    """Split text into chunks and save to DB with valid unique chunk_ids."""
    with app.app_context():
        # Get last numeric chunk_id safely
        last_chunk = (
            ServiceChunk.query
            .order_by(cast(func.substr(ServiceChunk.chunk_id, 3), Integer).desc())
            .first()
        )
        last_id = last_chunk.chunk_id if last_chunk else None

        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        for chunk_text in chunks:
            chunk_id = ServiceChunk.generate_id(last_id)
            last_id = chunk_id  # update for next

            new_chunk = ServiceChunk(
                chunk_id=chunk_id,
                service_record_id=service_record_id,
                text_chunk=chunk_text,
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(new_chunk)

        db.session.commit()
        print(f"{len(chunks)} chunk(s) saved successfully.")

# ===== Example run =====
if __name__ == "__main__":
    # Option 1: Record from mic
    # audio_data = record_audio(duration=5)
    # text = transcribe(audio_data)

    # Option 2: Transcribe existing audio file
    audio_file = "data/audio/LaguTerlaluCinta.mp3"
    text = transcribe(audio_file)

    # Save chunks to service_chunks
    save_chunks(service_record_id="SR0001", text=text)