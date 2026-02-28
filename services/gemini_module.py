import os, json
from google import genai

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def get_gemini_analysis(raw_transcript: str, genre: str) -> dict:
    prompt = f"""You are a music producer AI assistant.

A musician recorded a rough voice memo. Transcription:
"{raw_transcript}"

Genre: {genre}

Respond with ONLY valid JSON (no markdown):

{{
  "cleaned_lyrics": "polished singable version (1 verse + chorus max, short for 30s track)",
  "style_prompt": "detailed Lyria music prompt (genre, tempo BPM, mood, instruments, energy)",
  "detected_genre": "refined genre suggestion",
  "mood": "one word (e.g. melancholic, upbeat, nostalgic)",
  "bpm": 120,
  "key": "C minor"
}}"""

    response = _get_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)
