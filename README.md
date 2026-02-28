# MemoMuse

MemoMuse transforms rough voice memos into fully produced music demos. Record a rough idea, select a genre, and get a produced track with instrumentation and vocals.

## How It Works

1. **Record** — Hum, sing, or speak your idea into the browser
2. **Transcribe** — Whisper converts your audio to text
3. **Analyze** — Gemini extracts lyrics, mood, BPM, and a style prompt
4. **Refine** — Featherless AI polishes the lyrics (optional)
5. **Generate** — Lyria creates an instrumental while ElevenLabs synthesizes vocals, in parallel
6. **Mix** — pydub layers vocals over the instrumental and exports the final MP3

## Tech Stack

| Component | Service |
|---|---|
| Transcription | OpenAI Whisper |
| LLM Analysis | Google Gemini 2.0 Flash |
| Instrumental | Google Lyria Realtime |
| Vocals | ElevenLabs TTS |
| Lyric Refinement | Featherless AI (Qwen2.5-7B) |
| Session Memory | Backboard.io |
| Audio Processing | pydub |
| Server | FastAPI + uvicorn |

## Setup

### 1. Install System Dependencies

MemoMuse uses `pydub` which requires `ffmpeg` to process audio files.
On macOS:
```sh
brew install ffmpeg
```
On Ubuntu/Debian:
```sh
sudo apt update && sudo apt install ffmpeg
```

### 2. Create Virtual Environment & Install Python Dependencies

It is highly recommended to use a Python virtual environment to avoid conflicts.

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example env file and fill in your keys:

```sh
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI Studio key (Gemini + Lyria) |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key |
| `FEATHERLESS_API_KEY` | No | Featherless AI key |
| `BACKBOARD_API_KEY` | No | Backboard.io key |

### 4. Run the Server

Make sure your virtual environment is activated before running the server:

```sh
source venv/bin/activate
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Project Structure

```
MemoMuse/
├── main.py              # FastAPI entry point
├── pipeline.py          # 6-step orchestration pipeline
├── services/            # External service integrations
│   ├── transcribe_module.py
│   ├── gemini_module.py
│   ├── lyria_module.py
│   ├── elevenlabs_module.py
│   ├── featherless_module.py
│   ├── backboard_module.py
│   └── pianofi_module.py
├── static/
│   └── index.html       # Single-page frontend
└── requirements.txt
```
