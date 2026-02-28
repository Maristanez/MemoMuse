import os, json
from google import genai

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def get_gemini_analysis(raw_transcript: str, genre: str) -> dict:
    prompt = f"""You are a professional music producer and songwriter.

A musician recorded a rough voice memo. Transcription:
"{raw_transcript}"

Target genre: {genre}

First, determine if the transcript contains actual sung/spoken lyrics or is mostly humming/vocalizing (e.g. "hmm", "la la la", "na na", "doo doo", or empty/nonsensical text). Set contains_lyrics to false if it's humming/vocalizing, true if there are real words.

If contains_lyrics is true:
- Take their raw idea and turn it into FULL, polished, singable song lyrics.
- Expand the idea — add emotion, imagery, storytelling. Make it feel like a real song.
- Structure: Verse 1 (4-6 lines) → Chorus (4 lines) → Verse 2 (4-6 lines) → Chorus (4 lines).
- Keep the original message/feeling but elevate the language to fit the genre.

If contains_lyrics is false:
- Write original lyrics inspired by the mood/energy of their humming.
- Same structure: Verse 1 → Chorus → Verse 2 → Chorus.

Always create a detailed music production prompt for instrumental generation.

Respond with ONLY valid JSON (no markdown):

{{
  "contains_lyrics": true,
  "song_title": "A catchy, creative song title (2-5 words). Make it memorable and fitting for the genre.",
  "cleaned_lyrics": "Full structured lyrics with [Verse 1], [Chorus], [Verse 2], [Chorus] labels. 16-24 lines total.",
  "style_prompt": "Detailed music production prompt: genre, exact BPM, mood, key, instruments (list specific ones), energy arc, production style. Be very specific.",
  "detected_genre": "refined genre",
  "mood": "one or two words",
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
