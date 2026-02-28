import os, asyncio
from pydub import AudioSegment
from services.gemini_module import get_gemini_analysis
from services.elevenlabs_module import synthesize_vocals
from services.lyria_module import generate_instrumental
from services.transcribe_module import transcribe_audio
from services.backboard_module import store_session
from services.featherless_module import refine_lyrics

VOCAL_REDUCTION_DB = 3

async def run_pipeline(input_path: str, genre: str) -> str:
    os.makedirs("temp", exist_ok=True)

    # Step 1: Transcribe
    raw_transcript = transcribe_audio(input_path)
    print(f"[1/6] Transcription: {raw_transcript[:100]}...")

    # Step 2: Gemini analysis
    gemini_result = get_gemini_analysis(raw_transcript, genre)
    cleaned_lyrics = gemini_result["cleaned_lyrics"]
    style_prompt = gemini_result["style_prompt"]
    mood = gemini_result.get("mood", "neutral")
    bpm = gemini_result.get("bpm", 120)
    print(f"[2/6] Gemini: mood={mood}, bpm={bpm}")

    # Step 3: Backboard.io session memory (optional sponsor)
    try:
        await store_session(raw_transcript, cleaned_lyrics, style_prompt, genre, mood)
        print("[3/6] Backboard session stored")
    except Exception as e:
        print(f"[3/6] Backboard skipped: {e}")

    # Step 4: Featherless lyric refinement (optional sponsor)
    try:
        refined = refine_lyrics(cleaned_lyrics, genre, mood)
        if refined: cleaned_lyrics = refined
        print("[4/6] Featherless refined lyrics")
    except Exception as e:
        print(f"[4/6] Featherless skipped: {e}")

    # Step 5: Parallel generation — instrumental + vocals
    instrumental_task = asyncio.create_task(asyncio.to_thread(generate_instrumental, style_prompt, bpm))
    vocal_task = asyncio.create_task(asyncio.to_thread(synthesize_vocals, cleaned_lyrics))
    instrumental_path = await instrumental_task
    vocal_path = await vocal_task
    print("[5/6] Audio generated")

    # Step 6: Mix
    instrumental = AudioSegment.from_file(instrumental_path)
    vocal = AudioSegment.from_file(vocal_path) - VOCAL_REDUCTION_DB  # reduce vocal volume
    if len(vocal) > len(instrumental):
        vocal = vocal[:len(instrumental)]
    combined = instrumental.overlay(vocal, position=0)
    output_path = "temp/final_output.mp3"
    combined.export(output_path, format="mp3")
    print("[6/6] Final mix exported")
    return output_path
