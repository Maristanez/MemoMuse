from elevenlabs.client import ElevenLabs
import os

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    return _client


def convert_speech_to_speech(audio_path: str, output_path: str = "temp/vocals.mp3") -> str:
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
