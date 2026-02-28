import os, wave, asyncio
from google import genai
from google.genai import types


def generate_instrumental(style_prompt: str, bpm: int = 120, output_path: str = "temp/instrumental.wav") -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={"api_version": "v1alpha"})
    audio_chunks = []

    async def _generate():
        async with client.aio.live.music.connect(model="models/lyria-realtime-exp") as session:
            await session.set_weighted_prompts([types.WeightedPrompt(text=style_prompt, weight=1.0)])
            await session.set_music_generation_config(
                types.LiveMusicGenerationConfig(bpm=bpm, temperature=1.0, guidance=3.5)
            )
            await session.play()

            total_samples = 0
            target_samples = 48000 * 60  # 60 seconds at 48kHz
            print(f"Target samples: {target_samples}")
            async for message in session.receive():
                if message.server_content and message.server_content.audio_chunks:
                    for chunk in message.server_content.audio_chunks:
                        audio_chunks.append(chunk.data)
                        total_samples += len(chunk.data) // 4
                    print(f"Received chunk. Total samples: {total_samples}/{target_samples}")
                if total_samples >= target_samples:
                    print("Reached target samples!")
                    break
            print("Exited async for loop")

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_generate())
    finally:
        loop.close()

    with wave.open(output_path, "w") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        for chunk_data in audio_chunks:
            wav.writeframes(chunk_data)
    return output_path
