import sys
import os
import pathlib
import numpy as np
import parselmouth

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis_engine import load_audio_mono

FILES_TO_CHECK = ["samples_new/book/eggypp_male_UK.mp3"]


def analyze_single(f):
    path = pathlib.Path(__file__).parent.parent / f
    print(f"\n=== Deep Analysis of {path.name} ===")

    if not path.exists():
        print(f"File not found: {path}")
        return

    # 1. Load Audio
    y, sr = load_audio_mono(path)
    print(f"Loaded: len={len(y)}, sr={sr}")

    if len(y) == 0:
        print("Empty audio")
        return

    snd = parselmouth.Sound(y, sampling_frequency=sr)

    # 2. Intensity
    intensity = snd.to_intensity()
    max_intensity = intensity.values.max()
    print(f"Max Intensity: {max_intensity:.2f} dB")

    # 3. Harmonicity (HNR)
    try:
        harmonicity = snd.to_harmonicity(time_step=0.01, minimum_pitch=75.0)
        hnr_values = harmonicity.values
        hnr_values[hnr_values == -200] = np.nan
        mean_hnr = np.nanmean(hnr_values)
        max_hnr = np.nanmax(hnr_values)
        print(f"HNR Stats: Mean={mean_hnr:.2f} dB, Max={max_hnr:.2f} dB")
    except Exception as e:
        print(f"HNR Failed: {e}")

    # 4. Pitch (Wide Range)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=50.0, pitch_ceiling=1200.0)
    pitch_values = pitch.selected_array["frequency"]
    pitch_values = pitch_values[pitch_values > 0]

    if len(pitch_values) > 0:
        mean_pitch = np.mean(pitch_values)
        min_pitch = np.min(pitch_values)
        max_pitch = np.max(pitch_values)
        print(
            f"Pitch (50-1200Hz): Mean={mean_pitch:.1f}Hz, Min={min_pitch:.1f}Hz, Max={max_pitch:.1f}Hz"
        )
    else:
        print("Pitch (50-1200Hz): No pitch detected.")

    # 4b. Pitch (Standard)
    pitch_std = snd.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=600.0)
    pitch_std_values = pitch_std.selected_array["frequency"]
    pitch_std_values = pitch_std_values[pitch_std_values > 0]

    if len(pitch_std_values) > 0:
        print(f"Pitch (Standard 75-600): Detected {len(pitch_std_values)} frames.")
    else:
        print("Pitch (Standard 75-600): No pitch detected.")


def main():
    for f in FILES_TO_CHECK:
        analyze_single(f)


if __name__ == "__main__":
    main()
