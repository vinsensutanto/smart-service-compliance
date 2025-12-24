# scripts/stt_whisper.py
import whisper

# Load Whisper model once
model = whisper.load_model("base")  # You can switch to "small" or "medium"

def transcribe_chunk(audio_file, language="id"):
    """
    Transcribe a single audio file (or chunk) using Whisper.
    Returns text as string.
    """
    result = model.transcribe(audio_file, language=language)
    return result.get("text", "")

def record_audio(duration=5, fs=16000):
    """
    Record audio from microphone.
    Returns a NumPy array.
    """
    import sounddevice as sd
    import numpy as np

    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    return np.squeeze(audio)
