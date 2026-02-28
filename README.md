# MemoMuse

MemoMuse transforms rough voice memos into fully produced music demos — then lets you sell them as vinyl records. Record a rough idea, pick a genre, tweak the sound in the studio, and get a mixed track with vocals and instrumentation.

## How It Works

1. **Record** — Hum, sing, or speak your idea into the browser
2. **Transcribe** — Whisper converts your audio to text
3. **Analyze** — Gemini generates a song title, full lyrics, style prompt, mood, BPM, and key
4. **Refine** — Featherless AI polishes the lyrics (optional)
5. **Generate** — Lyria creates a 60-second instrumental while ElevenLabs synthesizes vocals, in parallel
6. **Mix** — pydub normalizes, applies studio EQ/pitch, layers vocals over instrumental, exports final MP3
7. **Publish** — One click creates a vinyl record product on your Shopify store

## Features

- **Studio Controls** — Pick from 20+ ElevenLabs voices, adjust bass/treble EQ, pitch shift (±6 semitones), and vocal/instrumental balance
- **Live Karaoke** — Lyrics highlighted line-by-line in real-time as the song plays
- **Vinyl Record** — Animated spinning disc with song title; "Buy as Vinyl" creates a real Shopify product ($24.99)
- **Smart Vocal Routing** — Gemini detects lyrics vs humming: TTS for lyrics, Speech-to-Speech for humming
- **Download & Copy** — One-click MP3 download and lyrics clipboard copy

## Tech Stack

| Component | Service |
|---|---|
| Transcription | OpenAI Whisper (local, base model) |
| LLM Analysis | Google Gemini 2.5 Flash |
| Instrumental | Google Lyria Realtime (experimental) |
| Vocals | ElevenLabs TTS / Speech-to-Speech |
| Voice Library | ElevenLabs Voices API (20+ voices) |
| Lyric Refinement | Featherless AI (Qwen2.5-7B-Instruct) |
| Session Memory | Backboard.io REST API |
| E-Commerce | Shopify Admin API |
| Audio Processing | pydub + FFmpeg |
| Server | Python 3, FastAPI + uvicorn |

## Setup

### 1. Install System Dependencies

```sh
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg
```

### 2. Install Python Dependencies

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example env file and fill in your keys:

```sh
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google AI Studio key (powers Gemini + Lyria) |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key (TTS, STS, voice library) |
| `ELEVENLABS_VOICE_ID` | No | Default voice ID (falls back to Rachel) |
| `FEATHERLESS_API_KEY` | No | Featherless AI lyric refinement |
| `BACKBOARD_API_KEY` | No | Backboard.io session memory |
| `SHOPIFY_ADMIN_TOKEN` | No | Shopify Admin API token (`write_products` scope) |
| `NEXT_PUBLIC_SHOPIFY_STORE_DOMAIN` | No | e.g. `yourstore.myshopify.com` |
| `SHOPIFY_STOREFRONT_TOKEN` | No | Shopify Storefront API token |

### 4. Run

```sh
source venv/bin/activate
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Single-page frontend |
| `POST` | `/generate` | Accepts audio + genre + studio params, runs pipeline, returns JSON |
| `GET` | `/audio/{filename}` | Serves generated MP3 files |
| `GET` | `/api/voices` | Returns available ElevenLabs voices |
| `POST` | `/api/publish` | Creates a vinyl product on Shopify |
| `GET` | `/api/config` | Returns Shopify storefront config |

## Project Structure

```
MemoMuse/
├── main.py                # FastAPI entry point (6 endpoints)
├── pipeline.py            # 6-step pipeline + audio post-processing (EQ, pitch)
├── services/
│   ├── transcribe_module.py   # Whisper transcription
│   ├── gemini_module.py       # Gemini analysis + song title
│   ├── lyria_module.py        # Lyria instrumental generation
│   ├── elevenlabs_module.py   # ElevenLabs TTS/STS + voice library
│   ├── featherless_module.py  # Featherless lyric refinement
│   ├── backboard_module.py    # Backboard.io session memory
│   ├── shopify_module.py      # Shopify product creation
│   └── pianofi_module.py      # Audio-to-MIDI (experimental)
├── static/
│   └── index.html             # Frontend (recording, studio, karaoke, vinyl)
├── tests/                     # Unit + integration tests
├── OVERVIEW.md                # Detailed technical overview
└── requirements.txt
```
