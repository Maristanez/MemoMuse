# MemoMuse

Voice memo to produced music demo pipeline with studio controls and Shopify vinyl integration. Record a rough idea, pick a genre, tweak the sound, get a mixed track with vocals and instrumentation, then sell it as a vinyl record.

## Architecture

FastAPI server (`main.py`) with endpoints for generation, voice library, Shopify publishing, and audio serving.

### Pipeline (`pipeline.py`) — 6 steps:
1. **Transcribe** — Whisper (base model) via `services/transcribe_module.py`
2. **Analyze** — Gemini 2.5 Flash extracts song title, cleaned lyrics, style prompt, mood, BPM, key, and detects lyrics vs humming via `services/gemini_module.py`
3. **Store session** — Backboard.io persistent memory (optional) via `services/backboard_module.py`
4. **Refine lyrics** — Featherless AI / Qwen model (optional) via `services/featherless_module.py`
5. **Generate audio** — Instrumental (Lyria realtime) + vocals (ElevenLabs TTS/STS with selectable voice) run in parallel via `services/lyria_module.py` and `services/elevenlabs_module.py`
6. **Mix + Post-process** — pydub normalizes, applies bass/treble EQ, pitch shift, vocal balance, overlays vocals on instrumental, exports final MP3

### Services (`services/`)
One module per external service integration. All imports go through `services.*`.
- `shopify_module.py` — Creates vinyl products on Shopify via Admin API

### Frontend
Single-page app at `static/index.html`. Records audio via MediaRecorder API, offers studio controls (voice picker, EQ, pitch, mix balance), posts to `/generate`, plays result with karaoke lyrics, and publishes to Shopify.

## Tech Stack

- **Runtime**: Python 3, FastAPI + uvicorn
- **Transcription**: OpenAI Whisper (`openai-whisper`)
- **LLM Analysis**: Google Gemini 2.5 Flash (`google-generativeai`)
- **Instrumental**: Google Lyria Realtime (`google-genai` v1alpha)
- **Vocals**: ElevenLabs TTS/STS + Voice Library (`elevenlabs`)
- **Lyric Refinement**: Featherless AI (OpenAI-compatible API, Qwen2.5-7B)
- **Session Memory**: Backboard.io REST API
- **E-Commerce**: Shopify Admin API (`requests`)
- **Audio Processing**: pydub + FFmpeg (EQ, pitch shift, normalization)

## Required Environment Variables

Set in `.env` (gitignored):
- `GEMINI_API_KEY` — Google AI Studio key (used by both Gemini and Lyria)
- `ELEVENLABS_API_KEY` — ElevenLabs API key (TTS, STS, voice library)
- `ELEVENLABS_VOICE_ID` — Default voice ID (optional)
- `FEATHERLESS_API_KEY` — Featherless AI key (optional)
- `BACKBOARD_API_KEY` — Backboard.io key (optional)
- `SHOPIFY_ADMIN_TOKEN` — Shopify Admin API token (optional)
- `NEXT_PUBLIC_SHOPIFY_STORE_DOMAIN` — Shopify store domain (optional)
- `SHOPIFY_STOREFRONT_TOKEN` — Shopify Storefront API token (optional)

## Running

```sh
pip install -r requirements.txt
python main.py # serves on http://localhost:8000
```

## Key Conventions

- Temp audio files go in `temp/` (gitignored, created at runtime)
- Service modules live in `services/`: one file per external service
- Optional integrations (Backboard, Featherless, Shopify) are wrapped in try/except so the pipeline works without them
- Lyria module uses `asyncio.new_event_loop()` because it runs inside `asyncio.to_thread`
- Studio controls (voice, EQ, pitch, mix) are passed as a JSON `studio` field in the generate form
- `load_dotenv(override=True)` ensures `.env` changes are always picked up on restart
