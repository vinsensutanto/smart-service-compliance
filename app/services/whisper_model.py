import whisper

_model = None

def get_whisper_model():
    global _model
    if _model is None:
        print("[WHISPER] Loading Whisper model...")
        _model = whisper.load_model("base")  # or "small"
    return _model
