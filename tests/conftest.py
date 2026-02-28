import pytest
from pydub import AudioSegment
from pydub.generators import Sine


@pytest.fixture
def tmp_audio_dir(tmp_path):
    """Provides a temporary directory for audio files."""
    return tmp_path


@pytest.fixture
def dummy_mp3(tmp_path):
    """Creates a short silent MP3 file for testing."""
    path = tmp_path / "dummy.mp3"
    AudioSegment.silent(duration=1000).export(str(path), format="mp3")
    return str(path)


@pytest.fixture
def dummy_wav(tmp_path):
    """Creates a short sine-wave WAV file for testing."""
    path = tmp_path / "dummy.wav"
    Sine(440).to_audio_segment(duration=1000).export(str(path), format="wav")
    return str(path)


@pytest.fixture
def sample_gemini_response():
    """Returns a realistic Gemini API response dict with contains_lyrics."""
    return {
        "contains_lyrics": True,
        "cleaned_lyrics": "Walking down the road today\nFeeling like I found my way",
        "style_prompt": "upbeat pop, 120 BPM, major key, acoustic guitar, light drums, cheerful energy",
        "detected_genre": "indie pop",
        "mood": "upbeat",
        "bpm": 120,
        "key": "C major",
    }
