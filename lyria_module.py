import os, wave
import asyncio
from google import genai
from google.genai import types

def generate_instrumental(style_prompt: str, bpm: int = 120) -> str:
    output_path = "temp/instrumental.wav"
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={'api_version': 'v1alpha'})
    audio_chunks = []

    async def _generate():
        session = await client.aio.live.music.connect(model="models/lyria-realtime-exp")
        await session.set_weighted_prompts([types.WeightedPrompt(text=style_prompt, weight=1.0)])
        await session.set_music_generation_config(types.MusicGenerationConfig(bpm=bpm, temperature=1.0, guidance=3.5))
        await session.play()

        total_samples = 0
        target_samples = 48000 * 30  # 30 seconds at 48kHz
        async for message in session.receive():
            if message.server_content and message.server_content.audio_chunks:
                for chunk in message.server_content.audio_chunks:
                    audio_chunks.append(chunk.data)
                    total_samples += len(chunk.data) // 4
            if total_samples >= target_samples:
                break
        await session.close()

    # Run in a fresh event loop (this function is always called from a thread via asyncio.to_thread)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate())
    finally:
        loop.close()

    with wave.open(output_path, 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        for chunk_data in audio_chunks:
            wav.writeframes(chunk_data)
    return output_path

# FALLBACK: audiocraft MusicGen locally
def generate_instrumental_fallback(style_prompt: str, bpm: int = 120) -> str:
    from audiocraft.models import MusicGen
    import torchaudio
    model = MusicGen.get_pretrained('facebook/musicgen-small')
    model.set_generation_params(duration=15)
    wav = model.generate([style_prompt])
    output_path = "temp/instrumental.wav"
    torchaudio.save(output_path, wav[0].cpu(), 32000)
    return output_path
