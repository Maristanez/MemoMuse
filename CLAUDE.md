# MemoMuse

Voice memo to produced music demo pipeline. Record a rough idea, pick a genre, get a mixed track with vocals and instrumentation.

## Architecture

FastAPI server (`main.py`) with a single `POST /generate` endpoint that accepts audio + genre, runs the pipeline, and returns an MP3.

### Pipeline (`pipeline.py`) — 6 steps:
1. **Transcribe** — Whisper (base model) via `services/transcribe_module.py`
2. **Analyze** — Gemini 2.0 Flash extracts cleaned lyrics, style prompt, mood, BPM, key via `services/gemini_module.py`
3. **Store session** — Backboard.io persistent memory (optional) via `services/backboard_module.py`
4. **Refine lyrics** — Featherless AI / Qwen model (optional) via `services/featherless_module.py`
5. **Generate audio** — Instrumental (Lyria realtime) + vocals (ElevenLabs TTS) run in parallel via `services/lyria_module.py` and `services/elevenlabs_module.py`
6. **Mix** — pydub overlays vocals on instrumental, exports final MP3

### Services (`services/`)
One module per external service integration. All imports go through `services.*`.

### Frontend
Single-page app at `static/index.html`. Records audio via MediaRecorder API, posts to `/generate`, plays result.

## Tech Stack

- **Runtime**: Python 3, FastAPI + uvicorn
- **Transcription**: OpenAI Whisper (`openai-whisper`)
- **LLM Analysis**: Google Gemini (`google-generativeai`)
- **Instrumental**: Google Lyria Realtime (`google-genai` v1alpha)
- **Vocals**: ElevenLabs TTS (`elevenlabs`)
- **Lyric Refinement**: Featherless AI (OpenAI-compatible API, Qwen2.5-7B)
- **Session Memory**: Backboard.io REST API
- **Audio Processing**: pydub
- **Fallback**: audiocraft MusicGen (local, commented out)

## Required Environment Variables

Set in `.env` (gitignored):
- `GEMINI_API_KEY` — Google AI Studio key (used by both Gemini and Lyria)
- `ELEVENLABS_API_KEY` — ElevenLabs API key
- `FEATHERLESS_API_KEY` — Featherless AI key (optional)
- `BACKBOARD_API_KEY` — Backboard.io key (optional)

## Running

```sh
pip install -r requirements.txt
python main.py  # serves on http://localhost:8000
```

## Key Conventions

- Temp audio files go in `temp/` (gitignored, created at runtime)
- Service modules live in `services/`: one file per external service
- Optional integrations (Backboard, Featherless) are wrapped in try/except so the pipeline works without them
- Lyria module uses `asyncio.new_event_loop()` because it runs inside `asyncio.to_thread`
