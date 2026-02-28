import os, asyncio, uuid
from pydub import AudioSegment
from services.gemini_module import get_gemini_analysis
from services.elevenlabs_module import convert_speech_to_speech, synthesize_vocals
from services.lyria_module import generate_instrumental
from services.transcribe_module import transcribe_audio
from services.backboard_module import store_session
from services.featherless_module import refine_lyrics

VOCAL_BOOST_DB = 6
INSTRUMENTAL_CUT_DB = 6


async def run_pipeline(input_path: str, genre: str) -> dict:
    os.makedirs("temp", exist_ok=True)
    run_id = uuid.uuid4().hex[:8]

    # Step 1: Transcribe
    raw_transcript = await asyncio.to_thread(transcribe_audio, input_path)
    print(f"[1/6] Transcription: {raw_transcript[:100]}...")

    # Step 2: Gemini analysis — full lyrics + style prompt + humming detection
    gemini_result = await asyncio.to_thread(get_gemini_analysis, raw_transcript, genre)
    cleaned_lyrics = gemini_result["cleaned_lyrics"]
    style_prompt = gemini_result["style_prompt"]
    mood = gemini_result.get("mood", "neutral")
    bpm = gemini_result.get("bpm", 120)
    if isinstance(bpm, str):
        bpm = int("".join(c for c in bpm if c.isdigit()) or "120")
    contains_lyrics = gemini_result.get("contains_lyrics", True)
    print(f"[2/6] Gemini: mood={mood}, bpm={bpm}, contains_lyrics={contains_lyrics}")
    print(f"      Lyrics preview: {cleaned_lyrics[:120]}...")

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
    # If user sang lyrics → TTS with expanded lyrics
    # If user hummed → STS to preserve their melody
    inst_path = f"temp/instrumental_{run_id}.wav"
    vocal_path = f"temp/vocals_{run_id}.mp3"
    instrumental_task = asyncio.create_task(
        asyncio.to_thread(generate_instrumental, style_prompt, bpm, inst_path)
    )
    if contains_lyrics:
        vocal_task = asyncio.create_task(
            asyncio.to_thread(synthesize_vocals, cleaned_lyrics, vocal_path)
        )
        print("      -> Using TTS with generated lyrics")
    else:
        vocal_task = asyncio.create_task(
            asyncio.to_thread(convert_speech_to_speech, input_path, vocal_path)
        )
        print("      -> Using STS to preserve hummed melody")
    inst_path = await instrumental_task
    try:
        vocal_path = await vocal_task
    except Exception as e:
        vocal_path = None
        print(f"[5/6] Vocal generation failed ({e}), falling back to instrumental only")

    if vocal_path:
        print("[5/6] Audio generated")
    else:
        print("[5/6] Instrumental generated (vocals skipped)")

    # Step 6: Mix — layer vocals over instrumental, or export instrumental only
    instrumental = AudioSegment.from_file(inst_path)

    if vocal_path:
        vocal = AudioSegment.from_file(vocal_path)

        # Normalize both to -20 dBFS then apply relative balance
        def normalize(seg, target_dbfs=-20.0):
            change = target_dbfs - seg.dBFS
            return seg.apply_gain(change)

        instrumental = normalize(instrumental) - INSTRUMENTAL_CUT_DB
        vocal = normalize(vocal) + VOCAL_BOOST_DB

        if len(vocal) > len(instrumental):
            vocal = vocal[: len(instrumental)]
        combined = instrumental.overlay(vocal, position=0)
    else:
        combined = instrumental

    output_path = f"temp/final_{run_id}.mp3"
    combined.export(output_path, format="mp3")
    print(f"[6/6] Final mix exported ({len(combined) / 1000:.1f}s)")

    # Cleanup intermediate files
    for p in [inst_path, vocal_path]:
        try:
            os.remove(p)
        except OSError:
            pass

    return {
        "output_path": output_path,
        "song_title": gemini_result.get("song_title", "Untitled Track"),
        "lyrics": cleaned_lyrics,
        "mood": mood,
        "bpm": bpm,
        "genre": gemini_result.get("detected_genre", genre),
        "key": gemini_result.get("key", ""),
    }
