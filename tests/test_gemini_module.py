"""Unit tests for services/gemini_module.py"""
import json
import pytest
from unittest.mock import patch, MagicMock


class TestGetGeminiAnalysis:
    """Tests for get_gemini_analysis JSON parsing and error handling."""

    @patch("services.gemini_module.genai")
    def test_parses_clean_json_response(self, mock_genai, sample_gemini_response):
        """Gemini returns clean JSON without markdown fences."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.return_value.text = json.dumps(sample_gemini_response)

        from services.gemini_module import get_gemini_analysis
        result = get_gemini_analysis("la la la feeling good", "pop")

        assert result["cleaned_lyrics"] == sample_gemini_response["cleaned_lyrics"]
        assert result["style_prompt"] == sample_gemini_response["style_prompt"]
        assert result["mood"] == "upbeat"
        assert result["bpm"] == 120

    @patch("services.gemini_module.genai")
    def test_strips_markdown_json_fences(self, mock_genai, sample_gemini_response):
        """Gemini wraps response in ```json ... ``` fences."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        wrapped = f"```json\n{json.dumps(sample_gemini_response)}\n```"
        mock_model.generate_content.return_value.text = wrapped

        from services.gemini_module import get_gemini_analysis
        result = get_gemini_analysis("la la la feeling good", "pop")

        assert result["cleaned_lyrics"] == sample_gemini_response["cleaned_lyrics"]
        assert result["bpm"] == 120

    @patch("services.gemini_module.genai")
    def test_strips_plain_markdown_fences(self, mock_genai, sample_gemini_response):
        """Gemini wraps response in ``` ... ``` without 'json' label."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        wrapped = f"```\n{json.dumps(sample_gemini_response)}\n```"
        mock_model.generate_content.return_value.text = wrapped

        from services.gemini_module import get_gemini_analysis
        result = get_gemini_analysis("humming a tune", "jazz")

        assert result["mood"] == "upbeat"

    @patch("services.gemini_module.genai")
    def test_raises_on_invalid_json(self, mock_genai):
        """Non-JSON response raises json.JSONDecodeError."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.return_value.text = "This is not JSON at all"

        from services.gemini_module import get_gemini_analysis
        with pytest.raises(json.JSONDecodeError):
            get_gemini_analysis("some lyrics", "pop")

    @patch("services.gemini_module.genai")
    def test_passes_genre_in_prompt(self, mock_genai):
        """Verifies the genre is included in the prompt sent to Gemini."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.return_value.text = json.dumps({
            "cleaned_lyrics": "test", "style_prompt": "test",
            "detected_genre": "jazz", "mood": "smooth", "bpm": 90, "key": "Bb major"
        })

        from services.gemini_module import get_gemini_analysis
        get_gemini_analysis("bah bah bah", "jazz")

        call_args = mock_model.generate_content.call_args[0][0]
        assert "jazz" in call_args

    @patch("services.gemini_module.genai")
    def test_handles_whitespace_around_json(self, mock_genai, sample_gemini_response):
        """JSON with leading/trailing whitespace is parsed correctly."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.return_value.text = f"  \n{json.dumps(sample_gemini_response)}\n  "

        from services.gemini_module import get_gemini_analysis
        result = get_gemini_analysis("test", "pop")

        assert result["bpm"] == 120
