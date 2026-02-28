"""Unit tests for services/transcribe_module.py"""
import pytest
from unittest.mock import patch, MagicMock


class TestTranscribeAudio:
    """Tests for transcribe_audio Whisper integration."""

    @patch("services.transcribe_module.whisper")
    def test_returns_transcription_text(self, mock_whisper):
        """Successful transcription returns the text field."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "hello world this is a test"}

        # Reset the cached model so our mock is used
        import services.transcribe_module as mod
        mod._model = None

        result = mod.transcribe_audio("test.webm")
        assert result == "hello world this is a test"

    @patch("services.transcribe_module.whisper")
    def test_loads_base_model(self, mock_whisper):
        """Whisper base model is loaded on first call."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "test"}

        import services.transcribe_module as mod
        mod._model = None

        mod.transcribe_audio("test.webm")
        mock_whisper.load_model.assert_called_once_with("base")

    @patch("services.transcribe_module.whisper")
    def test_caches_model_across_calls(self, mock_whisper):
        """Model is loaded once and reused for subsequent calls."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "test"}

        import services.transcribe_module as mod
        mod._model = None

        mod.transcribe_audio("a.webm")
        mod.transcribe_audio("b.webm")

        # load_model should only be called once due to caching
        mock_whisper.load_model.assert_called_once()
        assert mock_model.transcribe.call_count == 2

    @patch("services.transcribe_module.whisper")
    def test_passes_audio_path_to_whisper(self, mock_whisper):
        """The audio file path is forwarded to whisper.transcribe."""
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_model.transcribe.return_value = {"text": "test"}

        import services.transcribe_module as mod
        mod._model = None

        mod.transcribe_audio("/path/to/recording.webm")
        mock_model.transcribe.assert_called_with("/path/to/recording.webm")
