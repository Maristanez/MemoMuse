"""API tests for main.py — /generate endpoint via FastAPI TestClient."""

import os
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


DUMMY_PIPELINE_RESULT = {
    "output_path": "temp/final_test1234.mp3",
    "lyrics": "I walk alone tonight",
    "mood": "melancholic",
    "bpm": 120,
    "genre": "pop",
    "key": "A minor",
}


class TestGenerateEndpoint:

    @patch("main.run_pipeline", new_callable=AsyncMock, return_value=DUMMY_PIPELINE_RESULT)
    def test_returns_json_with_audio_url(self, mock_pipeline, client):
        os.makedirs("temp", exist_ok=True)
        with open("temp/final_test1234.mp3", "wb") as f:
            f.write(b"fake_mp3")

        try:
            response = client.post(
                "/generate",
                files={"audio": ("test.webm", b"fake_audio", "audio/webm")},
                data={"genre": "pop"},
            )

            assert response.status_code == 200
            body = response.json()
            assert body["audio_url"] == "/audio/final_test1234.mp3"
            assert body["lyrics"] == "I walk alone tonight"
            assert body["mood"] == "melancholic"
            assert body["bpm"] == 120
            assert body["genre"] == "pop"
            assert body["key"] == "A minor"
        finally:
            try:
                os.remove("temp/final_test1234.mp3")
            except OSError:
                pass

    @patch("main.run_pipeline", new_callable=AsyncMock, return_value=DUMMY_PIPELINE_RESULT)
    def test_default_genre_is_pop(self, mock_pipeline, client):
        os.makedirs("temp", exist_ok=True)
        with open("temp/final_test1234.mp3", "wb") as f:
            f.write(b"fake_mp3")

        try:
            client.post(
                "/generate",
                files={"audio": ("test.webm", b"fake_audio", "audio/webm")},
            )
            call_args = mock_pipeline.call_args[0]
            assert call_args[1] == "pop"
        finally:
            try:
                os.remove("temp/final_test1234.mp3")
            except OSError:
                pass

    @patch("main.run_pipeline", new_callable=AsyncMock, side_effect=RuntimeError("boom"))
    def test_returns_500_on_error(self, mock_pipeline, client):
        response = client.post(
            "/generate",
            files={"audio": ("test.webm", b"fake_audio", "audio/webm")},
            data={"genre": "rock"},
        )
        assert response.status_code == 500
        assert "boom" in response.json()["error"]

    def test_missing_audio_returns_422(self, client):
        response = client.post("/generate", data={"genre": "pop"})
        assert response.status_code == 422


class TestRootEndpoint:

    def test_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "MemoMuse" in response.text
