"""Integration tests for pipeline.py — verifies orchestration order and data flow."""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
from pydub import AudioSegment


@pytest.fixture
def mock_services(tmp_path):
    """Patches all service modules and returns the mocks + temp audio files."""
    # Create real audio files so pydub can load them
    instrumental_path = str(tmp_path / "instrumental.wav")
    vocal_path = str(tmp_path / "vocals.mp3")

    tone = AudioSegment.silent(duration=2000)
    tone.export(instrumental_path, format="wav")
    tone.export(vocal_path, format="mp3")

    patches = {
        "transcribe": patch("pipeline.transcribe_audio", return_value="raw transcript text"),
        "gemini": patch("pipeline.get_gemini_analysis", return_value={
            "cleaned_lyrics": "cleaned lyrics here",
            "style_prompt": "upbeat pop 120bpm",
            "mood": "happy",
            "bpm": 120,
        }),
        "backboard": patch("pipeline.store_session", new_callable=AsyncMock),
        "featherless": patch("pipeline.refine_lyrics", return_value="refined lyrics here"),
        "lyria": patch("pipeline.generate_instrumental", return_value=instrumental_path),
        "elevenlabs": patch("pipeline.synthesize_vocals", return_value=vocal_path),
    }

    mocks = {}
    for name, p in patches.items():
        mocks[name] = p.start()

    yield mocks, tmp_path

    for p in patches.values():
        p.stop()


class TestRunPipeline:
    """Integration tests for the 6-step pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_mp3(self, mock_services):
        """Pipeline runs all 6 steps and returns a path to the final MP3."""
        mocks, tmp_path = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            result = await run_pipeline("input.webm", "pop")

        assert result == "temp/final_output.mp3"

    @pytest.mark.asyncio
    async def test_step1_transcription_called_with_input(self, mock_services):
        """Step 1: transcribe_audio is called with the input path."""
        mocks, _ = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("my_recording.webm", "pop")

        mocks["transcribe"].assert_called_once_with("my_recording.webm")

    @pytest.mark.asyncio
    async def test_step2_gemini_receives_transcript_and_genre(self, mock_services):
        """Step 2: Gemini analysis gets the raw transcript and genre."""
        mocks, _ = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "jazz")

        mocks["gemini"].assert_called_once_with("raw transcript text", "jazz")

    @pytest.mark.asyncio
    async def test_step3_backboard_called_with_session_data(self, mock_services):
        """Step 3: Backboard store_session is called with correct args."""
        mocks, _ = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        mocks["backboard"].assert_called_once_with(
            "raw transcript text", "cleaned lyrics here",
            "upbeat pop 120bpm", "pop", "happy"
        )

    @pytest.mark.asyncio
    async def test_step3_backboard_failure_does_not_halt_pipeline(self, mock_services):
        """Pipeline continues even if Backboard raises an exception."""
        mocks, _ = mock_services
        mocks["backboard"].side_effect = Exception("Backboard down")

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            result = await run_pipeline("input.webm", "pop")

        assert result == "temp/final_output.mp3"

    @pytest.mark.asyncio
    async def test_step4_featherless_refines_lyrics(self, mock_services):
        """Step 4: Featherless refine_lyrics is called with cleaned lyrics."""
        mocks, _ = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        mocks["featherless"].assert_called_once_with(
            "cleaned lyrics here", "pop", "happy"
        )

    @pytest.mark.asyncio
    async def test_step4_featherless_failure_uses_original_lyrics(self, mock_services):
        """If Featherless fails, original cleaned lyrics are used for vocals."""
        mocks, _ = mock_services
        mocks["featherless"].side_effect = Exception("Featherless down")

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        # synthesize_vocals should receive the original cleaned lyrics
        mocks["elevenlabs"].assert_called_once_with("cleaned lyrics here")

    @pytest.mark.asyncio
    async def test_step4_featherless_none_uses_original_lyrics(self, mock_services):
        """If Featherless returns None, original cleaned lyrics are used."""
        mocks, _ = mock_services
        mocks["featherless"].return_value = None

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        mocks["elevenlabs"].assert_called_once_with("cleaned lyrics here")

    @pytest.mark.asyncio
    async def test_step5_parallel_generation(self, mock_services):
        """Step 5: Both instrumental and vocal generation are called."""
        mocks, _ = mock_services

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        mocks["lyria"].assert_called_once_with("upbeat pop 120bpm", 120)
        mocks["elevenlabs"].assert_called_once_with("refined lyrics here")

    @pytest.mark.asyncio
    async def test_step5_vocals_use_refined_lyrics(self, mock_services):
        """When Featherless succeeds, vocals use the refined lyrics."""
        mocks, _ = mock_services
        mocks["featherless"].return_value = "polished version of lyrics"

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        mocks["elevenlabs"].assert_called_once_with("polished version of lyrics")

    @pytest.mark.asyncio
    async def test_defaults_when_gemini_omits_optional_fields(self, mock_services):
        """Pipeline uses defaults (mood=neutral, bpm=120) if Gemini omits them."""
        mocks, _ = mock_services
        mocks["gemini"].return_value = {
            "cleaned_lyrics": "lyrics",
            "style_prompt": "style",
            # mood and bpm intentionally omitted
        }

        from pipeline import run_pipeline
        with patch("pipeline.os.makedirs"):
            await run_pipeline("input.webm", "pop")

        # Should use default bpm=120
        mocks["lyria"].assert_called_once_with("style", 120)
