"""API tests for main.py FastAPI endpoints."""
import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from pydub import AudioSegment


@pytest.fixture
def dummy_output_mp3(tmp_path):
    """Creates a dummy MP3 that run_pipeline will 'return'."""
    path = str(tmp_path / "final_output.mp3")
    AudioSegment.silent(duration=1000).export(path, format="mp3")
    return path


@pytest.fixture
def client():
    """Provides a FastAPI TestClient."""
    from main import app
    return TestClient(app)


class TestGenerateEndpoint:
    """Tests for POST /generate."""

    @patch("main.run_pipeline", new_callable=AsyncMock)
    def test_returns_200_with_audio(self, mock_pipeline, client, dummy_output_mp3):
        """Successful generation returns 200 with audio/mpeg content."""
        mock_pipeline.return_value = dummy_output_mp3

        # Create a fake audio upload
        response = client.post(
            "/generate",
            files={"audio": ("recording.webm", b"fake audio data", "audio/webm")},
            data={"genre": "pop"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"

    @patch("main.run_pipeline", new_callable=AsyncMock)
    def test_default_genre_is_pop(self, mock_pipeline, client, dummy_output_mp3):
        """When no genre is specified, defaults to 'pop'."""
        mock_pipeline.return_value = dummy_output_mp3

        client.post(
            "/generate",
            files={"audio": ("recording.webm", b"fake audio data", "audio/webm")},
        )

        call_args = mock_pipeline.call_args[0]
        assert call_args[1] == "pop"  # genre argument

    @patch("main.run_pipeline", new_callable=AsyncMock)
    def test_passes_genre_to_pipeline(self, mock_pipeline, client, dummy_output_mp3):
        """Custom genre is forwarded to run_pipeline."""
        mock_pipeline.return_value = dummy_output_mp3

        client.post(
            "/generate",
            files={"audio": ("recording.webm", b"fake audio data", "audio/webm")},
            data={"genre": "jazz"},
        )

        call_args = mock_pipeline.call_args[0]
        assert call_args[1] == "jazz"

    @patch("main.run_pipeline", new_callable=AsyncMock)
    def test_saves_uploaded_file_to_temp(self, mock_pipeline, client, dummy_output_mp3):
        """Uploaded audio is saved to the temp directory."""
        mock_pipeline.return_value = dummy_output_mp3

        client.post(
            "/generate",
            files={"audio": ("recording.webm", b"fake audio data", "audio/webm")},
            data={"genre": "pop"},
        )

        # First arg to run_pipeline should be a temp path
        input_path = mock_pipeline.call_args[0][0]
        assert input_path.startswith("temp/input_")
        assert input_path.endswith(".webm")

    @patch("main.run_pipeline", new_callable=AsyncMock)
    def test_pipeline_error_raises(self, mock_pipeline, client):
        """Internal pipeline error propagates as an exception."""
        mock_pipeline.side_effect = Exception("Something broke")

        with pytest.raises(Exception, match="Something broke"):
            client.post(
                "/generate",
                files={"audio": ("recording.webm", b"fake audio data", "audio/webm")},
                data={"genre": "pop"},
            )

    def test_missing_audio_returns_422(self, client):
        """Request without audio file returns 422 validation error."""
        response = client.post("/generate", data={"genre": "pop"})
        assert response.status_code == 422


class TestRootEndpoint:
    """Tests for GET /."""

    def test_returns_html(self, client):
        """Root endpoint serves the index.html file."""
        response = client.get("/")
        assert response.status_code == 200
        assert "MemoMuse" in response.text
