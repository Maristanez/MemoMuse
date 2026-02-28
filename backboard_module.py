import os, aiohttp

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY")
BACKBOARD_BASE_URL = "https://app.backboard.io/api"
_assistant_id = None
_thread_id = None

async def store_session(transcript: str, lyrics: str, prompt: str, genre: str, mood: str):
    """Store session in Backboard.io for persistent memory across generations."""
    global _assistant_id, _thread_id
    headers = {"Authorization": f"Bearer {BACKBOARD_API_KEY}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        if not _assistant_id:
            async with session.post(f"{BACKBOARD_BASE_URL}/assistants", headers=headers, json={
                "name": "MemoMuse Music Producer",
                "system_prompt": "You are a music production assistant. Remember user preferences and musical style choices.",
                "llm_provider": "google", "llm_model_name": "gemini-2.0-flash"
            }) as resp:
                _assistant_id = (await resp.json()).get("assistant_id")

        if not _thread_id:
            async with session.post(f"{BACKBOARD_BASE_URL}/threads", headers=headers,
                json={"assistant_id": _assistant_id}) as resp:
                _thread_id = (await resp.json()).get("thread_id")

        context = (f"Voice memo. Genre: {genre}, Mood: {mood}. "
                   f"Transcript: {transcript[:200]}. Lyrics: {lyrics[:200]}. Prompt: {prompt[:200]}.")

        async with session.post(f"{BACKBOARD_BASE_URL}/threads/{_thread_id}/messages", headers=headers,
            json={"content": context, "memory": "Auto"}) as resp:
            return await resp.json()
