import requests, os

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

def refine_lyrics(lyrics: str, genre: str, mood: str) -> str:
    """Refine lyrics via Featherless AI (OpenAI-compatible, 4300+ open-source models)."""
    response = requests.post("https://api.featherless.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {FEATHERLESS_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [
                {"role": "system", "content": "You are a professional songwriter. Refine lyrics to be singable and genre-appropriate. 4-8 lines max. Return ONLY refined lyrics."},
                {"role": "user", "content": f"Genre: {genre}\nMood: {mood}\n\nOriginal:\n{lyrics}\n\nRefined:"}
            ],
            "max_tokens": 200, "temperature": 0.7
        }, timeout=15)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    return None
