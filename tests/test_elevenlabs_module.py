"""Unit tests for services/elevenlabs_module.py — TTS vs STS routing."""

import os
from unittest.mock import patch, MagicMock

from elevenlabs import VoiceSettings

from services.elevenlabs_module import synthesize_vocals, convert_speech_to_speech


class TestSynthesizeVocals:
    """Tests for the TTS path (synthesize_vocals)."""

    @patch("services.elevenlabs_module._get_client")
    def test_uses_tts_model(self, mock_get_client, tmp_path):
        mock_get_client().text_to_speech.convert.return_value = [b"audio"]
        out = str(tmp_path / "vocals.mp3")

        synthesize_vocals("test lyrics", out)

        mock_get_client().text_to_speech.convert.assert_called_once_with(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            text="test lyrics",
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.3,
                similarity_boost=0.75,
                style=0.45,
                use_speaker_boost=True,
            ),
        )

    @patch("services.elevenlabs_module._get_client")
    def test_writes_all_chunks(self, mock_get_client, tmp_path):
        mock_get_client().text_to_speech.convert.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        out = str(tmp_path / "vocals.mp3")

        synthesize_vocals("lyrics", out)

        with open(out, "rb") as f:
            assert f.read() == b"chunk1chunk2chunk3"

    @patch("services.elevenlabs_module._get_client")
    def test_returns_output_path(self, mock_get_client, tmp_path):
        mock_get_client().text_to_speech.convert.return_value = [b"data"]
        out = str(tmp_path / "vocals.mp3")

        result = synthesize_vocals("lyrics", out)

        assert result == out
        assert os.path.exists(out)


class TestConvertSpeechToSpeech:
    """Tests for the STS path (convert_speech_to_speech)."""

    @patch("services.elevenlabs_module._get_client")
    def test_uses_sts_model(self, mock_get_client, tmp_path):
        mock_get_client().speech_to_speech.convert.return_value = [b"sts_audio"]
        audio_in = str(tmp_path / "input.webm")
        with open(audio_in, "wb") as f:
            f.write(b"dummy")
        out = str(tmp_path / "vocals.mp3")

        convert_speech_to_speech(audio_in, out)

        call_kwargs = mock_get_client().speech_to_speech.convert.call_args.kwargs
        assert call_kwargs["voice_id"] == "21m00Tcm4TlvDq8ikWAM"
        assert call_kwargs["model_id"] == "eleven_multilingual_sts_v2"

    @patch("services.elevenlabs_module._get_client")
    def test_writes_all_chunks(self, mock_get_client, tmp_path):
        mock_get_client().speech_to_speech.convert.return_value = [b"sts1", b"sts2"]
        audio_in = str(tmp_path / "input.webm")
        with open(audio_in, "wb") as f:
            f.write(b"dummy")
        out = str(tmp_path / "vocals.mp3")

        convert_speech_to_speech(audio_in, out)

        with open(out, "rb") as f:
            assert f.read() == b"sts1sts2"

    @patch("services.elevenlabs_module._get_client")
    def test_returns_output_path(self, mock_get_client, tmp_path):
        mock_get_client().speech_to_speech.convert.return_value = [b"data"]
        audio_in = str(tmp_path / "input.webm")
        with open(audio_in, "wb") as f:
            f.write(b"dummy")
        out = str(tmp_path / "vocals.mp3")

        result = convert_speech_to_speech(audio_in, out)

        assert result == out
        assert os.path.exists(out)
