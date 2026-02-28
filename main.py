import os
from dotenv import load_dotenv
load_dotenv()  # must run before importing pipeline (service modules read env at import time)

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pipeline import run_pipeline
import uuid

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/generate")
async def generate(audio: UploadFile = File(...), genre: str = Form(default="pop")):
    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/input_{uuid.uuid4().hex}.webm"
    with open(input_path, "wb") as f:
        f.write(await audio.read())
    output_path = await run_pipeline(input_path, genre)
    return FileResponse(output_path, media_type="audio/mpeg", filename="output.mp3")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
