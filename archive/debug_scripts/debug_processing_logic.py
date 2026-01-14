import sys
import os
import pathlib
import io
import librosa
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.audio_processing import process_audio_data

FILE_PATH = "samples_new/ear/MichaelDS_male_UK.mp3"


def debug_processing():
    path = pathlib.Path(__file__).parent.parent / FILE_PATH
    print(f"\n=== Debugging Processing Logic for {path.name} ===")

    if not path.exists():
        print(f"File not found: {path}")
        return

    # Read Raw Bytes
    with open(path, "rb") as f:
        raw_bytes = f.read()

    print(f"Raw File Size: {len(raw_bytes)} bytes")

    # Run Processing
    try:
        processed_bytes = process_audio_data(raw_bytes)
        print(f"Processed File Size: {len(processed_bytes)} bytes")

        # Load processed bytes to check duration
        y, sr = librosa.load(io.BytesIO(processed_bytes), sr=None)
        print(f"Processed Audio: Duration={len(y)/sr:.3f}s, Samples={len(y)}, SR={sr}")

        if len(y) == 0:
            print("!!! Processed audio is EMPTY !!!")
        else:
            print(f"Max Amplitude: {np.max(np.abs(y)):.4f}")

    except Exception as e:
        print(f"Processing Failed: {e}")

    # Verify Analysis on Processed Data
    try:
        from analysis_engine import find_syllable_nucleus
        import parselmouth

        # We need to recreate the sound object from y and sr since find_syllable_nucleus expects Parselmouth Sound
        # Note: y is float32, parselmouth might want float64 or specific format?
        y_float = y.astype(np.float64)
        snd = parselmouth.Sound(y_float, sampling_frequency=sr)

        print("\n--- Analysing PROCESSED Audio ---")
        seg = find_syllable_nucleus(snd, pitch_floor=75, pitch_ceiling=600)
        print(f"Syllable Nucleus: {seg}")

    except ImportError:
        print("Skipping analysis check (analysis_engine not found in path)")
    except Exception as e:
        print(f"Analysis Check Failed: {e}")


if __name__ == "__main__":
    debug_processing()
