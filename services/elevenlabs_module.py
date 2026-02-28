from elevenlabs.client import ElevenLabs
import os

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def synthesize_vocals(lyrics: str) -> str:
    audio = client.text_to_speech.convert(
        voice_id="21m00Tcm4TlvDq8ikWAM",  # "Rachel"
        text=lyrics,
        model_id="eleven_multilingual_v2",
        voice_settings={"stability": 0.4, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True}
    )
    output_path = "temp/vocals.mp3"
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return output_path
