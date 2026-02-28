from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import os

_client = None
_voices_cache = None


def _get_client():
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    return _client


def get_voices() -> list[dict]:
    """Fetch available voices from ElevenLabs library."""
    global _voices_cache
    if _voices_cache is not None:
        return _voices_cache

    response = _get_client().voices.get_all()
    voices = []
    for v in response.voices:
        labels = v.labels or {}
        voices.append({
            "voice_id": v.voice_id,
            "name": v.name,
            "accent": labels.get("accent", ""),
            "gender": labels.get("gender", ""),
            "age": labels.get("age", ""),
            "description": labels.get("description", ""),
            "preview_url": v.preview_url or "",
        })
    _voices_cache = voices
    return voices


def synthesize_vocals(lyrics: str, output_path: str = "temp/vocals.mp3", voice_id: str = None,
                      stability: float = 0.3, similarity: float = 0.75, style: float = 0.45) -> str:
    """Generate vocal track from lyrics using TTS."""
    if not voice_id:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    audio = _get_client().text_to_speech.convert(
        voice_id=voice_id,
        text=lyrics,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=style,
            use_speaker_boost=True,
        ),
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path


def convert_speech_to_speech(audio_path: str, output_path: str = "temp/vocals.mp3", voice_id: str = None) -> str:
    """Clean up raw voice recording via speech-to-speech."""
    if not voice_id:
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    with open(audio_path, "rb") as audio_file:
        audio = _get_client().speech_to_speech.convert(
            voice_id=voice_id,
            audio=audio_file,
            model_id="eleven_multilingual_sts_v2",
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
    return output_path
