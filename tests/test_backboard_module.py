"""Unit tests for services/backboard_module.py"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from aiohttp import ClientSession


class TestStoreSession:
    """Tests for store_session Backboard.io integration."""

    @pytest.mark.asyncio
    @patch("services.backboard_module.aiohttp.ClientSession")
    async def test_creates_assistant_and_thread_on_first_call(self, mock_session_cls):
        """First call creates an assistant, a thread, then posts a message."""
        # Reset module-level state
        import services.backboard_module as mod
        mod._assistant_id = None
        mod._thread_id = None

        # Mock the context manager and responses
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Assistant creation response
        assistant_resp = AsyncMock()
        assistant_resp.json = AsyncMock(return_value={"assistant_id": "ast_123"})

        # Thread creation response
        thread_resp = AsyncMock()
        thread_resp.json = AsyncMock(return_value={"thread_id": "thr_456"})

        # Message post response
        msg_resp = AsyncMock()
        msg_resp.json = AsyncMock(return_value={"message_id": "msg_789"})

        # Chain the three post calls
        post_contexts = [assistant_resp, thread_resp, msg_resp]
        mock_posts = []
        for resp in post_contexts:
            ctx = AsyncMock()
            ctx.__aenter__ = AsyncMock(return_value=resp)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_posts.append(ctx)

        mock_session.post = MagicMock(side_effect=mock_posts)

        result = await mod.store_session("transcript", "lyrics", "prompt", "pop", "upbeat")

        assert mock_session.post.call_count == 3
        assert result == {"message_id": "msg_789"}

    @pytest.mark.asyncio
    @patch("services.backboard_module.aiohttp.ClientSession")
    async def test_reuses_assistant_and_thread_on_second_call(self, mock_session_cls):
        """Second call skips assistant/thread creation, only posts message."""
        import services.backboard_module as mod
        mod._assistant_id = "ast_existing"
        mod._thread_id = "thr_existing"

        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        msg_resp = AsyncMock()
        msg_resp.json = AsyncMock(return_value={"message_id": "msg_999"})

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=msg_resp)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=ctx)

        result = await mod.store_session("t", "l", "p", "pop", "happy")

        # Only one post call (the message), no assistant/thread creation
        mock_session.post.assert_called_once()
        assert result == {"message_id": "msg_999"}

    @pytest.mark.asyncio
    @patch("services.backboard_module.aiohttp.ClientSession")
    async def test_truncates_long_context_fields(self, mock_session_cls):
        """Context fields are truncated to 200 chars each."""
        import services.backboard_module as mod
        mod._assistant_id = "ast_1"
        mod._thread_id = "thr_1"

        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        msg_resp = AsyncMock()
        msg_resp.json = AsyncMock(return_value={})
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=msg_resp)
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=ctx)

        long_text = "x" * 500
        await mod.store_session(long_text, long_text, long_text, "pop", "happy")

        call_kwargs = mock_session.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        # Each field is truncated to [:200], so total content is bounded
        assert len(payload["content"]) < 700
