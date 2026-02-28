from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn, traceback, json
from dotenv import load_dotenv
from pipeline import run_pipeline
from services.shopify_module import create_vinyl_product
from services.elevenlabs_module import get_voices
import os, uuid
from google import genai
from google.genai import types
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

from dotenv import load_dotenv
load_dotenv(override=True)

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
ssl.create_default_context = ssl._create_unverified_context

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/generate")
async def generate(audio: UploadFile = File(...), genre: str = Form(default="pop"),
                   studio: str = Form(default="{}")):
    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/input_{uuid.uuid4().hex}.webm"
    with open(input_path, "wb") as f:
        f.write(await audio.read())
    try:
        studio_params = json.loads(studio) if studio else {}
    except (json.JSONDecodeError, TypeError):
        studio_params = {}
    try:
        result = await run_pipeline(input_path, genre, studio_params)
        filename = os.path.basename(result["output_path"])
        return JSONResponse({
            "audio_url": f"/audio/{filename}",
            "song_title": result["song_title"],
            "lyrics": result["lyrics"],
            "mood": result["mood"],
            "bpm": result["bpm"],
            "genre": result["genre"],
            "key": result["key"],
        })
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/voices")
async def list_voices():
    """Return available ElevenLabs voices."""
    try:
        voices = get_voices()
        return JSONResponse(voices)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    path = f"temp/{filename}"
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(path, media_type="audio/mpeg", filename="MemoMuse_Track.mp3")


@app.post("/api/publish")
async def publish_vinyl(request: Request):
    """Create a vinyl record product on Shopify for the generated song."""
    try:
        body = await request.json()
        result = create_vinyl_product(
            song_title=body.get("song_title", "Untitled Track"),
            lyrics=body.get("lyrics", ""),
            genre=body.get("genre", ""),
            mood=body.get("mood", ""),
            bpm=body.get("bpm", 120),
            key=body.get("key", ""),
            audio_url=body.get("audio_url", ""),
        )
        if "error" in result:
            return JSONResponse(status_code=400, content=result)
        return JSONResponse(result)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/config")
async def get_config():
    return JSONResponse({
        "shopify_domain": os.getenv("NEXT_PUBLIC_SHOPIFY_STORE_DOMAIN", ""),
        "shopify_token": os.getenv("SHOPIFY_STOREFRONT_TOKEN", ""),
    })


@app.get("/voicemail")
async def voicemail_page():
    return FileResponse("static/voicemail.html")


@app.post("/api/voicemail/analyze")
async def voicemail_analyze(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    raw_mime = file.content_type or "audio/mpeg"
    supported_mimes = [
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg",
        "audio/webm", "audio/mp4", "audio/x-m4a",
    ]
    mime_type = raw_mime if raw_mime in supported_mimes else "audio/mpeg"

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    system_prompt = (
        "You are an assistant that analyzes customer support voicemails for a Shopify-like online store. "
        "Listen to the audio carefully and output strict JSON with exactly these fields: "
        "transcript, intent, sentiment, urgency, summary, suggestedReply. "
        "intent must be one of: ORDER_STATUS, RETURN, GENERAL_QUESTION, COMPLAINT, OTHER. "
        "sentiment must be one of: POSITIVE, NEUTRAL, NEGATIVE. "
        "urgency must be one of: LOW, MEDIUM, HIGH. "
        "Return ONLY valid JSON — no markdown code blocks, no explanation, no extra text."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            system_prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return JSONResponse(json.loads(text))


@app.post("/api/voicemail/tts")
async def voicemail_tts(request: Request):
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse(status_code=400, content={"error": "No text provided"})
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    audio_chunks = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    audio_bytes = b"".join(audio_chunks)
    return Response(audio_bytes, media_type="audio/mpeg")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
