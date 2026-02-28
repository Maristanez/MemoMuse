import os, aiohttp

_assistant_id = None
_thread_id = None


async def store_session(transcript: str, lyrics: str, prompt: str, genre: str, mood: str):
    """Store session in Backboard.io for persistent memory across generations."""
    global _assistant_id, _thread_id
    api_key = os.getenv("BACKBOARD_API_KEY")
    if not api_key:
        return
    base_url = "https://app.backboard.io/api"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        if not _assistant_id:
            async with session.post(f"{base_url}/assistants", headers=headers, json={
                "name": "MemoMuse Music Producer",
                "system_prompt": "You are a music production assistant. Remember user preferences and musical style choices.",
                "llm_provider": "google", "llm_model_name": "gemini-2.5-flash"
            }) as resp:
                _assistant_id = (await resp.json()).get("assistant_id")

        if not _thread_id:
            async with session.post(f"{base_url}/threads", headers=headers,
                json={"assistant_id": _assistant_id}) as resp:
                _thread_id = (await resp.json()).get("thread_id")

        context = (f"Voice memo. Genre: {genre}, Mood: {mood}. "
                   f"Transcript: {transcript[:200]}. Lyrics: {lyrics[:200]}. Prompt: {prompt[:200]}.")

        async with session.post(f"{base_url}/threads/{_thread_id}/messages", headers=headers,
            json={"content": context, "memory": "Auto"}) as resp:
            return await resp.json()
