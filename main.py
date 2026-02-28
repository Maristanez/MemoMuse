from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, traceback
from dotenv import load_dotenv
from pipeline import run_pipeline
from services.shopify_module import create_vinyl_product
import os, uuid

from dotenv import load_dotenv
load_dotenv(override=True)

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
ssl.create_default_context = ssl._create_unverified_context

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/generate")
async def generate(audio: UploadFile = File(...), genre: str = Form(default="pop")):
    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/input_{uuid.uuid4().hex}.webm"
    with open(input_path, "wb") as f:
        f.write(await audio.read())
    try:
        result = await run_pipeline(input_path, genre)
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


@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
