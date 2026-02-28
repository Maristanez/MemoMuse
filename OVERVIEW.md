# MemoMuse — Technical Overview

> Voice memo → produced music demo → vinyl on Shopify. Record a rough idea, pick a genre, tweak with studio controls, get a mixed track with vocals and instrumentation, then sell it as a vinyl record.

---

## Architecture

```
                         ┌──────────────────────────────────────────────┐
                         │              Frontend (index.html)           │
                         │  Record audio · Pick genre · Studio controls│
                         │  Karaoke lyrics · Vinyl display · Buy vinyl │
                         └────────────┬───────────────┬────────────────┘
                                      │               │
                              POST /generate    POST /api/publish
                              + studio params         │
                         ┌────────────▼───────────────▼────────────────┐
                         │          FastAPI (main.py)                   │
                         │                                              │
                         │  GET /api/voices ──► ElevenLabs voice lib    │
                         └────────────┬────────────────────────────────┘
                                      │
                         ┌────────────▼────────────────────────────────┐
                         │          Pipeline (pipeline.py)              │
                         │                                              │
                         │  1. Transcribe ──► Whisper (local)           │
                         │  2. Analyze ─────► Gemini 2.5 Flash          │
                         │  3. Store ───────► Backboard.io (optional)   │
                         │  4. Refine ──────► Featherless AI (optional) │
                         │  5. Generate ────► Lyria + ElevenLabs ║      │
                         │                    (parallel)         ║      │
                         │  6. Mix + EQ ────► pydub (bass/treble/pitch) │
                         └─────────────────────────────────────────────┘
```

---

## Pipeline — Step by Step

| Step | Service | What happens |
|------|---------|-------------|
| **1. Transcribe** | OpenAI Whisper (base, local) | Raw audio → text transcript |
| **2. Analyze** | Google Gemini 2.5 Flash | Transcript → song title, cleaned lyrics (Verse/Chorus structure, 16–24 lines), style prompt, mood, BPM, key, and `contains_lyrics` detection (real words vs humming) |
| **3. Store session** | Backboard.io REST API | Persists session context (transcript, lyrics, genre, mood) for memory across runs. Optional — pipeline continues if unavailable |
| **4. Refine lyrics** | Featherless AI (Qwen2.5-7B) | LLM polish pass on lyrics. Optional — original lyrics used if unavailable |
| **5. Generate audio** | Google Lyria Realtime + ElevenLabs | **Instrumental**: Lyria generates 60s at 48 kHz from the style prompt. **Vocals**: user-selected voice from ElevenLabs library with configurable stability/similarity/style; if lyrics detected → TTS, if humming → STS preserves melody. Both run in parallel. Falls back to instrumental-only if vocals fail |
| **6. Mix + Post-process** | pydub | Both tracks normalized to −20 dBFS. Vocal balance adjusted by user slider. Bass/treble EQ applied. Pitch shifted if requested. Overlay, trim, export final MP3 |

---

## Studio Controls

The frontend exposes a collapsible "Studio Controls" panel that passes parameters to the pipeline:

| Control | Range | What it does |
|---------|-------|-------------|
| **Voice** | 20+ ElevenLabs voices | Selects the vocal voice (male, female, various accents). Preview button plays a sample |
| **Bass** | -10 to +10 | Low-frequency EQ — boosts/cuts under 250 Hz via low-pass filter overlay |
| **Treble** | -10 to +10 | High-frequency EQ — boosts/cuts above 4 kHz via high-pass filter overlay |
| **Pitch** | -6 to +6 semitones | Shifts the final mix up/down via sample rate manipulation |
| **Vocal Mix** | -6 to +6 dB | Adjusts vocal/instrumental balance (positive = louder vocals) |

All parameters are JSON-serialized in the `studio` form field of `POST /generate`.

---

## Sponsor / API Integrations

### Google — Gemini + Lyria
- **Gemini 2.5 Flash** (`google-generativeai`): LLM analysis — extracts song title, lyrics, style prompt, mood, BPM, key, and determines if input is lyrics or humming
- **Lyria Realtime** (`google-genai` v1alpha): Experimental real-time music generation via async WebSocket. Generates 60-second instrumentals from a style prompt + BPM

### ElevenLabs — Voices + TTS + Speech-to-Speech
- **Voice Library** (`/api/voices`): Fetches all available voices with metadata (name, gender, accent, preview URL). Cached after first call
- **TTS** (`eleven_multilingual_v2`): Synthesizes generated lyrics into vocal audio. Accepts per-request voice ID and voice settings (stability, similarity, style)
- **STS** (`eleven_multilingual_sts_v2`): When the user hums instead of singing lyrics, preserves the original melody while applying the selected voice
- Voice selection enables "artist voice" simulation — pick different vocal characters for each track

### Shopify — Admin API
- Creates a **vinyl record product** on a Shopify store for each generated song
- Product includes: song title, $24.99 price, full lyrics in description, genre/mood/BPM/key metadata, "MemoMuse" vendor tag
- Uses OAuth-acquired Admin API token with `write_products` scope
- Frontend "Buy as Vinyl" button triggers creation, waits for CDN propagation, then opens the product page

### Backboard.io — Session Memory
- Stores each session's context (transcript, lyrics, prompt, genre, mood) via REST API
- Creates assistant + thread on first call, reuses thread for subsequent calls
- Enables persistent memory across pipeline runs
- Optional — wrapped in try/except

### Featherless AI — Lyric Refinement
- OpenAI-compatible API endpoint running **Qwen2.5-7B-Instruct**
- Takes raw Gemini lyrics + genre/mood and returns polished version
- Optional — original lyrics used if service is unavailable

### OpenAI Whisper — Transcription
- Runs locally (base model, ~150 MB)
- Transcribes user's voice recording to text
- Model is cached globally to avoid reloading between requests

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the single-page frontend |
| `POST` | `/generate` | Accepts `audio` + `genre` + `studio` (JSON), runs pipeline, returns `audio_url`, `song_title`, `lyrics`, `mood`, `bpm`, `genre`, `key` |
| `GET` | `/audio/{filename}` | Serves generated MP3 files from `temp/` |
| `GET` | `/api/voices` | Returns available ElevenLabs voices (id, name, gender, accent, preview URL) |
| `POST` | `/api/publish` | Creates a vinyl product on Shopify. Returns `product_url` |
| `GET` | `/api/config` | Returns Shopify storefront domain + token for the frontend |

---

## Frontend Features

- **Audio recording** — MediaRecorder API with live waveform visualizer (40 animated bars)
- **Genre picker** — 8 genre chips: Pop, Lo-Fi, Hip Hop, Cinematic, R&B, Indie Folk, Electronic, Jazz
- **Studio controls** — Collapsible panel: voice selector (20+ voices with preview), bass/treble EQ, pitch shift, vocal mix balance
- **Pipeline progress** — 4-step animated indicator (Transcribe → Analyze → Generate → Mix)
- **Custom audio player** — Plays the generated track with metadata pills (genre, mood, BPM, key)
- **Live karaoke display** — Lyrics highlighted line-by-line in sync with playback, auto-scrolling, with animated EQ bars
- **Vinyl record visual** — CSS-animated spinning disc with song title and genre label; spins during playback
- **Buy as Vinyl** — Creates a real Shopify product and opens the store page after CDN propagation
- **Download MP3** — One-click download named after the song title
- **Copy Lyrics** — Copies generated lyrics to clipboard
- **Dark glassmorphism theme** — Animated gradients, scroll-triggered reveals, responsive layout

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3, FastAPI, uvicorn |
| Transcription | OpenAI Whisper (local, base model) |
| LLM Analysis | Google Gemini 2.5 Flash |
| Instrumental | Google Lyria Realtime (experimental) |
| Vocals | ElevenLabs TTS / STS + Voice Library |
| Lyric Refinement | Featherless AI (Qwen2.5-7B-Instruct) |
| Session Memory | Backboard.io REST API |
| E-Commerce | Shopify Admin API |
| Audio Processing | pydub + FFmpeg (EQ, pitch shift, normalization) |
| Frontend | Vanilla HTML/CSS/JS, MediaRecorder API |

---

## Environment Variables

```
GEMINI_API_KEY          # Google AI Studio — powers Gemini + Lyria
ELEVENLABS_API_KEY      # ElevenLabs TTS/STS + voice library
ELEVENLABS_VOICE_ID     # Optional — default voice ID
FEATHERLESS_API_KEY     # Optional — Featherless AI lyric refinement
BACKBOARD_API_KEY       # Optional — Backboard.io session memory
SHOPIFY_ADMIN_TOKEN     # Shopify Admin API (OAuth token, write_products scope)
NEXT_PUBLIC_SHOPIFY_STORE_DOMAIN  # e.g. yourstore.myshopify.com
SHOPIFY_STOREFRONT_TOKEN          # Shopify Storefront API token
```

---

## Running

```bash
pip install -r requirements.txt
# Ensure ffmpeg is installed (brew install ffmpeg / apt install ffmpeg)
python main.py  # serves on http://localhost:8000
```

---

## Key Design Decisions

- **Conditional vocal routing**: Gemini detects lyrics vs humming → TTS for lyrics, STS for humming. Ensures the right approach for each input type
- **Voice selection**: ElevenLabs library exposes 20+ voices — users can pick male/female, different accents, and preview before generating
- **Studio post-processing**: Bass/treble EQ via pydub low/high-pass filter overlays; pitch shift via sample rate manipulation — all applied after mix
- **Parallel generation**: Instrumental and vocal tasks run simultaneously via `asyncio.create_task`, cutting generation time nearly in half
- **Graceful degradation**: Backboard, Featherless, and vocals are all wrapped in try/except. If any fail, the pipeline continues with what it has
- **Audio normalization**: Both tracks normalized to −20 dBFS before applying user-adjusted vocal balance for consistent clarity
- **Unique file IDs**: Each pipeline run uses `uuid4` hex for temp files, preventing race conditions on concurrent requests
- **Shopify CDN delay**: Frontend waits 8 seconds after product creation before opening the store URL, ensuring the product is purchasable
