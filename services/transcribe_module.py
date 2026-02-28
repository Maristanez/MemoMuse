import whisper

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcribe_audio(audio_path: str) -> str:
    return _get_model().transcribe(audio_path)["text"]
