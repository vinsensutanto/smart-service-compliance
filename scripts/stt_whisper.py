# app/services/stt_whisper.py
from app.services.whisper_model import get_whisper_model
import whisper
import librosa
import numpy as np
import sounddevice as sd

TARGET_SR = 16000

def _ensure_16k(file_path):
    """
    Load audio and guarantee 16kHz mono float32.
    """
    audio, sr = librosa.load(
        file_path,
        sr=TARGET_SR,
        mono=True
    )
    return audio.astype(np.float32)

def transcribe(file_path, language="id"):
    model = get_whisper_model()
    audio = _ensure_16k(file_path)

    result = model.transcribe(
        audio,
        language=language,
        verbose=False
    )
    return result


def transcribe_chunk(audio_file, language="id", initial_prompt=None):
    model = get_whisper_model()
    audio = _ensure_16k(audio_file)

    kwargs = {
        "language": language,
        "verbose": False,
        "temperature": 0.0,
    }

    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt

    result = model.transcribe(audio, **kwargs)
    return result.get("text", "").strip()


def record_audio(duration=5, fs=16000):
    """
    Record audio from microphone.
    Returns a NumPy array.
    """
    audio = sd.rec(
        int(duration * fs),
        samplerate=fs,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return np.squeeze(audio)
