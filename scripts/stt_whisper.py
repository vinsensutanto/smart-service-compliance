# app/services/stt_whisper.py
from app.services.whisper_model import get_whisper_model


def transcribe(file_path, language="id"):
    """
    Transcribe a full audio file using Whisper.
    """
    model = get_whisper_model()
    result = model.transcribe(file_path, language=language)
    return result


def transcribe_chunk(audio_file, language="id"):
    """
    Transcribe a single audio chunk.
    Returns text only.
    """
    model = get_whisper_model()
    result = model.transcribe(audio_file, language=language)
    return result.get("text", "").strip()


def record_audio(duration=5, fs=16000):
    """
    Record audio from microphone.
    Returns a NumPy array.
    """
    import sounddevice as sd
    import numpy as np

    audio = sd.rec(
        int(duration * fs),
        samplerate=fs,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return np.squeeze(audio)
