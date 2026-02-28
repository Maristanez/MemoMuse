import os, asyncio, uuid
from pydub import AudioSegment
from services.gemini_module import get_gemini_analysis
from services.elevenlabs_module import convert_speech_to_speech
from services.lyria_module import generate_instrumental
from services.transcribe_module import transcribe_audio
from services.backboard_module import store_session
from services.featherless_module import refine_lyrics

VOCAL_REDUCTION_DB = 3


async def run_pipeline(input_path: str, genre: str) -> str:
    os.makedirs("temp", exist_ok=True)
    run_id = uuid.uuid4().hex[:8]

    # Step 1: Transcribe (CPU-bound — run in thread to avoid blocking event loop)
    raw_transcript = await asyncio.to_thread(transcribe_audio, input_path)
    print(f"[1/6] Transcription: {raw_transcript[:100]}...")

    # Step 2: Gemini analysis (network I/O — run in thread)
    gemini_result = await asyncio.to_thread(get_gemini_analysis, raw_transcript, genre)
    cleaned_lyrics = gemini_result["cleaned_lyrics"]
    style_prompt = gemini_result["style_prompt"]
    mood = gemini_result.get("mood", "neutral")
    bpm = gemini_result.get("bpm", 120)
    if isinstance(bpm, str):
        bpm = int("".join(c for c in bpm if c.isdigit()) or "120")
    print(f"[2/6] Gemini: mood={mood}, bpm={bpm}")

    # Step 3: Backboard.io session memory (optional)
    try:
        await store_session(raw_transcript, cleaned_lyrics, style_prompt, genre, mood)
        print("[3/6] Backboard session stored")
    except Exception as e:
        print(f"[3/6] Backboard skipped: {e}")

    # Step 4: Featherless lyric refinement (optional)
    try:
        refined = await asyncio.to_thread(refine_lyrics, cleaned_lyrics, genre, mood)
        if refined:
            cleaned_lyrics = refined
        print("[4/6] Featherless refined lyrics")
    except Exception as e:
        print(f"[4/6] Featherless skipped: {e}")

    # Step 5: Parallel generation — instrumental + vocals
    inst_path = f"temp/instrumental_{run_id}.wav"
    vocal_path = f"temp/vocals_{run_id}.mp3"
    instrumental_task = asyncio.create_task(
        asyncio.to_thread(generate_instrumental, style_prompt, bpm, inst_path)
    )
    vocal_task = asyncio.create_task(
        asyncio.to_thread(convert_speech_to_speech, input_path, vocal_path)
    )
    inst_path = await instrumental_task
    vocal_path = await vocal_task
    print("[5/6] Audio generated")

    # Step 6: Mix
    instrumental = AudioSegment.from_file(inst_path)
    vocal = AudioSegment.from_file(vocal_path) - VOCAL_REDUCTION_DB
    if len(vocal) > len(instrumental):
        vocal = vocal[: len(instrumental)]
    combined = instrumental.overlay(vocal, position=0)
    output_path = f"temp/final_{run_id}.mp3"
    combined.export(output_path, format="mp3")
    print("[6/6] Final mix exported")

    # Cleanup intermediate files
    for p in [input_path, inst_path, vocal_path]:
        try:
            os.remove(p)
        except OSError:
            pass

    return output_path
