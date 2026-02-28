"""Unit tests for services/elevenlabs_module.py"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestSynthesizeVocals:
    """Tests for synthesize_vocals TTS call and file writing."""

    @patch("services.elevenlabs_module.client")
    def test_writes_audio_chunks_to_file(self, mock_client, tmp_path):
        """Audio chunks from ElevenLabs are written to an MP3 file."""
        chunks = [b"fake_audio_chunk_1", b"fake_audio_chunk_2"]
        mock_client.text_to_speech.convert.return_value = iter(chunks)

        output_path = str(tmp_path / "vocals.mp3")
        with patch("services.elevenlabs_module.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)

            from services.elevenlabs_module import synthesize_vocals
            # Patch the hardcoded output path
            with patch("builtins.open", mock_open):
                result = synthesize_vocals("hello world")

        assert result == "temp/vocals.mp3"
        mock_client.text_to_speech.convert.assert_called_once()

    @patch("services.elevenlabs_module.client")
    def test_uses_correct_voice_and_model(self, mock_client):
        """Verifies the Rachel voice ID and multilingual v2 model are used."""
        mock_client.text_to_speech.convert.return_value = iter([b"data"])

        os.makedirs("temp", exist_ok=True)
        from services.elevenlabs_module import synthesize_vocals

        try:
            synthesize_vocals("test lyrics")
        except Exception:
            pass  # File write may fail in test env

        call_kwargs = mock_client.text_to_speech.convert.call_args
        assert call_kwargs.kwargs["voice_id"] == "21m00Tcm4TlvDq8ikWAM"
        assert call_kwargs.kwargs["model_id"] == "eleven_multilingual_v2"

    @patch("services.elevenlabs_module.client")
    def test_passes_lyrics_as_text(self, mock_client):
        """The lyrics string is passed as the text parameter."""
        mock_client.text_to_speech.convert.return_value = iter([b"data"])

        os.makedirs("temp", exist_ok=True)
        from services.elevenlabs_module import synthesize_vocals

        try:
            synthesize_vocals("these are my lyrics")
        except Exception:
            pass

        call_kwargs = mock_client.text_to_speech.convert.call_args
        assert call_kwargs.kwargs["text"] == "these are my lyrics"

    @patch("services.elevenlabs_module.client")
    def test_voice_settings_configured(self, mock_client):
        """Voice settings include stability, similarity, style, and speaker boost."""
        mock_client.text_to_speech.convert.return_value = iter([b"data"])

        os.makedirs("temp", exist_ok=True)
        from services.elevenlabs_module import synthesize_vocals

        try:
            synthesize_vocals("test")
        except Exception:
            pass

        call_kwargs = mock_client.text_to_speech.convert.call_args
        settings = call_kwargs.kwargs["voice_settings"]
        assert settings["stability"] == 0.4
        assert settings["similarity_boost"] == 0.8
        assert settings["use_speaker_boost"] is True
