from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import os

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    return _client


def synthesize_vocals(lyrics: str, output_path: str = "temp/vocals.mp3") -> str:
    """Generate vocal track from lyrics using TTS."""
    audio = _get_client().text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        text=lyrics,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.3,
            similarity_boost=0.75,
            style=0.45,
            use_speaker_boost=True,
        ),
    )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path


def convert_speech_to_speech(audio_path: str, output_path: str = "temp/vocals.mp3") -> str:
    """Clean up raw voice recording via speech-to-speech."""
    with open(audio_path, "rb") as audio_file:
        audio = _get_client().speech_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            audio=audio_file,
            model_id="eleven_multilingual_sts_v2",
        )
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path
