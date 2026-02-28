"""Unit tests for services/gemini_module.py — JSON parsing and contains_lyrics detection."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.gemini_module import get_gemini_analysis


def _mock_response(text: str) -> MagicMock:
    """Create a fake Gemini response with the given .text."""
    resp = MagicMock()
    resp.text = text
    return resp


class TestContainsLyricsDetection:
    """Tests for the contains_lyrics field in Gemini's response."""

    @patch("services.gemini_module._get_client")
    def test_contains_lyrics_true_for_real_words(self, mock_get_client):
        payload = {
            "contains_lyrics": True,
            "cleaned_lyrics": "I walk alone tonight",
            "style_prompt": "pop upbeat 120bpm guitar",
            "detected_genre": "pop",
            "mood": "melancholic",
            "bpm": 120,
            "key": "A minor",
        }
        mock_get_client().models.generate_content.return_value = _mock_response(json.dumps(payload))

        result = get_gemini_analysis("I walk alone tonight under the stars", "pop")

        assert result["contains_lyrics"] is True
        assert result["cleaned_lyrics"] == "I walk alone tonight"

    @patch("services.gemini_module._get_client")
    def test_contains_lyrics_false_for_humming(self, mock_get_client):
        payload = {
            "contains_lyrics": False,
            "cleaned_lyrics": "",
            "style_prompt": "jazz smooth 90bpm saxophone",
            "detected_genre": "jazz",
            "mood": "dreamy",
            "bpm": 90,
            "key": "C major",
        }
        mock_get_client().models.generate_content.return_value = _mock_response(json.dumps(payload))

        result = get_gemini_analysis("hmm hmm la la la", "jazz")

        assert result["contains_lyrics"] is False
        assert result["cleaned_lyrics"] == ""


class TestJsonParsing:
    """Tests for JSON parsing and markdown fence stripping."""

    @patch("services.gemini_module._get_client")
    def test_parses_clean_json(self, mock_get_client, sample_gemini_response):
        mock_get_client().models.generate_content.return_value = _mock_response(
            json.dumps(sample_gemini_response)
        )

        result = get_gemini_analysis("la la la feeling good", "pop")

        assert result["cleaned_lyrics"] == sample_gemini_response["cleaned_lyrics"]
        assert result["mood"] == "upbeat"
        assert result["bpm"] == 120

    @patch("services.gemini_module._get_client")
    def test_strips_markdown_json_fences(self, mock_get_client, sample_gemini_response):
        wrapped = f"```json\n{json.dumps(sample_gemini_response)}\n```"
        mock_get_client().models.generate_content.return_value = _mock_response(wrapped)

        result = get_gemini_analysis("la la la", "pop")

        assert result["bpm"] == 120

    @patch("services.gemini_module._get_client")
    def test_strips_plain_markdown_fences(self, mock_get_client, sample_gemini_response):
        wrapped = f"```\n{json.dumps(sample_gemini_response)}\n```"
        mock_get_client().models.generate_content.return_value = _mock_response(wrapped)

        result = get_gemini_analysis("humming a tune", "jazz")

        assert result["mood"] == "upbeat"

    @patch("services.gemini_module._get_client")
    def test_raises_on_invalid_json(self, mock_get_client):
        mock_get_client().models.generate_content.return_value = _mock_response("This is not JSON")

        with pytest.raises(json.JSONDecodeError):
            get_gemini_analysis("some lyrics", "pop")

    @patch("services.gemini_module._get_client")
    def test_handles_whitespace_around_json(self, mock_get_client, sample_gemini_response):
        padded = f"  \n{json.dumps(sample_gemini_response)}\n  "
        mock_get_client().models.generate_content.return_value = _mock_response(padded)

        result = get_gemini_analysis("test", "pop")

        assert result["bpm"] == 120

    @patch("services.gemini_module._get_client")
    def test_all_expected_fields_present(self, mock_get_client, sample_gemini_response):
        mock_get_client().models.generate_content.return_value = _mock_response(
            json.dumps(sample_gemini_response)
        )

        result = get_gemini_analysis("test", "pop")

        for key in ("contains_lyrics", "cleaned_lyrics", "style_prompt",
                     "detected_genre", "mood", "bpm", "key"):
            assert key in result
