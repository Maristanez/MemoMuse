from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, traceback
from dotenv import load_dotenv
from pipeline import run_pipeline
import os, uuid

from dotenv import load_dotenv
load_dotenv()

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


@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
