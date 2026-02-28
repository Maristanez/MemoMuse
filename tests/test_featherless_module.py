"""Unit tests for services/featherless_module.py"""
import pytest
from unittest.mock import patch, MagicMock


class TestRefineLyrics:
    """Tests for refine_lyrics HTTP calls and response handling."""

    @patch("services.featherless_module.requests.post")
    def test_successful_refinement(self, mock_post):
        """200 response returns refined lyrics string."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "  Refined lyrics here  "}}]
        }
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        result = refine_lyrics("rough lyrics", "pop", "upbeat")

        assert result == "Refined lyrics here"
        mock_post.assert_called_once()

    @patch("services.featherless_module.requests.post")
    def test_returns_none_on_server_error(self, mock_post):
        """500 response returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        result = refine_lyrics("rough lyrics", "pop", "upbeat")

        assert result is None

    @patch("services.featherless_module.requests.post")
    def test_returns_none_on_rate_limit(self, mock_post):
        """429 rate limit response returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        result = refine_lyrics("rough lyrics", "pop", "upbeat")

        assert result is None

    @patch("services.featherless_module.requests.post")
    def test_returns_none_on_unauthorized(self, mock_post):
        """401 unauthorized returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        result = refine_lyrics("rough lyrics", "pop", "upbeat")

        assert result is None

    @patch("services.featherless_module.requests.post")
    def test_sends_correct_payload(self, mock_post):
        """Verifies the request body includes genre, mood, and lyrics."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "refined"}}]
        }
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        refine_lyrics("walking down the street", "hip hop", "melancholic")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        user_msg = payload["messages"][1]["content"]
        assert "hip hop" in user_msg
        assert "melancholic" in user_msg
        assert "walking down the street" in user_msg

    @patch("services.featherless_module.requests.post")
    def test_uses_correct_model(self, mock_post):
        """Verifies the Qwen model is specified in the request."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "refined"}}]
        }
        mock_post.return_value = mock_resp

        from services.featherless_module import refine_lyrics
        refine_lyrics("test", "pop", "happy")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["model"] == "Qwen/Qwen2.5-7B-Instruct"

    @patch("services.featherless_module.requests.post")
    def test_timeout_raises_exception(self, mock_post):
        """Network timeout propagates as an exception."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        from services.featherless_module import refine_lyrics
        with pytest.raises(requests.exceptions.Timeout):
            refine_lyrics("test", "pop", "happy")
