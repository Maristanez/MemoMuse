"""
Pianofi (pianofi.ca) — audio-to-MIDI/sheet-music transcription.
Check with sponsors at event for API endpoint. Fallback: basic-pitch.
"""
import subprocess, os

def extract_melody(audio_path: str) -> str:
    midi_dir = "temp/"
    os.makedirs(midi_dir, exist_ok=True)
    try:
        subprocess.run(["basic-pitch", midi_dir, audio_path], check=True, capture_output=True, timeout=30)
        base = os.path.splitext(os.path.basename(audio_path))[0]
        midi_path = os.path.join(midi_dir, f"{base}_basic_pitch.mid")
        if os.path.exists(midi_path): return midi_path
    except Exception as e:
        print(f"basic-pitch failed: {e}")
    try:
        subprocess.run(["python", "-m", "basic_pitch", midi_dir, audio_path], check=True, capture_output=True, timeout=30)
    except Exception as e:
        print(f"basic-pitch module failed: {e}")
    return None
