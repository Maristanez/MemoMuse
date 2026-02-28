"""Integration tests for pipeline.py — verifies TTS/STS conditional routing."""

import os
import pytest
from unittest.mock import patch, AsyncMock
from pydub import AudioSegment

from pipeline import run_pipeline


def _make_dummy_audio(path):
    """Write a minimal audio file so pydub can load it."""
    fmt = "wav" if path.endswith(".wav") else "mp3"
    AudioSegment.silent(duration=1000).export(path, format=fmt)


def _side_effect_instrumental(style_prompt, bpm, output_path):
    _make_dummy_audio(output_path)
    return output_path


def _side_effect_tts(lyrics, output_path):
    _make_dummy_audio(output_path)
    return output_path


def _side_effect_sts(audio_path, output_path):
    _make_dummy_audio(output_path)
    return output_path


HUMMING_GEMINI = {
    "contains_lyrics": False,
    "cleaned_lyrics": "",
    "style_prompt": "jazz smooth 90bpm saxophone mellow",
    "detected_genre": "jazz",
    "mood": "dreamy",
    "bpm": 90,
    "key": "C major",
}

LYRICS_GEMINI = {
    "contains_lyrics": True,
    "cleaned_lyrics": "I walk alone tonight under the stars",
    "style_prompt": "pop upbeat 120bpm guitar synth",
    "detected_genre": "pop",
    "mood": "melancholic",
    "bpm": 120,
    "key": "A minor",
}


class TestHummingRouting:
    """When contains_lyrics is False, pipeline routes to STS."""

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=HUMMING_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="hmm hmm la la la")
    async def test_sts_called_tts_not_called(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        await run_pipeline(input_file, "jazz")

        mock_sts.assert_called_once()
        assert mock_sts.call_args[0][0] == input_file
        mock_tts.assert_not_called()

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=HUMMING_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="hmm hmm")
    async def test_instrumental_gets_correct_params(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        result = await run_pipeline(input_file, "jazz")

        args = mock_instrumental.call_args[0]
        assert args[0] == "jazz smooth 90bpm saxophone mellow"
        assert args[1] == 90
        assert result["mood"] == "dreamy"
        assert result["bpm"] == 90


class TestLyricsRouting:
    """When contains_lyrics is True, pipeline routes to TTS."""

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=LYRICS_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="I walk alone tonight")
    async def test_tts_called_sts_not_called(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        await run_pipeline(input_file, "pop")

        mock_tts.assert_called_once()
        assert mock_tts.call_args[0][0] == "I walk alone tonight under the stars"
        mock_sts.assert_not_called()

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value="polished lyrics")
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=LYRICS_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="I walk alone tonight")
    async def test_tts_uses_refined_lyrics_when_available(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        await run_pipeline(input_file, "pop")

        mock_tts.assert_called_once()
        assert mock_tts.call_args[0][0] == "polished lyrics"


class TestPipelineOutput:
    """Verify the pipeline produces the expected output."""

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=LYRICS_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="hello world")
    async def test_returns_dict_with_output_path(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        result = await run_pipeline(input_file, "pop")

        assert "output_path" in result
        assert os.path.exists(result["output_path"])
        assert result["mood"] == "melancholic"
        assert result["bpm"] == 120
        assert result["genre"] == "pop"

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock, side_effect=Exception("down"))
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value=LYRICS_GEMINI)
    @patch("pipeline.transcribe_audio", return_value="hello")
    async def test_backboard_failure_does_not_halt(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        result = await run_pipeline(input_file, "pop")

        assert "output_path" in result

    @pytest.mark.asyncio
    @patch("pipeline.refine_lyrics", return_value=None)
    @patch("pipeline.store_session", new_callable=AsyncMock)
    @patch("pipeline.generate_instrumental", side_effect=_side_effect_instrumental)
    @patch("pipeline.convert_speech_to_speech", side_effect=_side_effect_sts)
    @patch("pipeline.synthesize_vocals", side_effect=_side_effect_tts)
    @patch("pipeline.get_gemini_analysis", return_value={
        "contains_lyrics": True,
        "cleaned_lyrics": "lyrics",
        "style_prompt": "style",
    })
    @patch("pipeline.transcribe_audio", return_value="test")
    async def test_defaults_when_gemini_omits_optional_fields(
        self, mock_transcribe, mock_gemini, mock_tts, mock_sts,
        mock_instrumental, mock_store, mock_refine, tmp_path
    ):
        """Pipeline uses defaults (mood=neutral, bpm=120) if Gemini omits them."""
        input_file = str(tmp_path / "input.webm")
        with open(input_file, "wb") as f:
            f.write(b"dummy")

        result = await run_pipeline(input_file, "pop")

        assert result["mood"] == "neutral"
        assert result["bpm"] == 120
