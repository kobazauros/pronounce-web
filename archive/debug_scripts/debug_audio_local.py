import sys
import os
import pathlib
import numpy as np
import parselmouth

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis_engine import (
    analyze_formants_from_path,
    load_audio_mono,
    find_syllable_nucleus,
    measure_formants,
)

# Files to test
TEST_CASES = [
    # {
    #     "path": "samples_new/hot/TopQuark_male_UK.mp3",
    #     "vowel": "ɒ",  # hot
    #     "word": "hot",
    # },
    {
        "path": "samples_new/cat/MichaelDS_male_UK.mp3",
        "vowel": "æ",  # cat
        "word": "cat",
    },
    # {"path": "samples_new/cup/eggypp_male_UK.mp3", "vowel": "ʌ", "word": "cup"},  # cup
]


def debug_file(item):
    path = pathlib.Path(__file__).parent.parent / item["path"]
    vowel = item["vowel"]
    print(f"\n=== Debugging {item['word']} ({path.name}) ===")

    if not path.exists():
        print(f"File not found: {path}")
        return

    # 1. Load Audio
    y, sr = load_audio_mono(path)
    print(f"Loaded: len={len(y)}, sr={sr}")

    if len(y) == 0:
        print("Error: Audio loaded empty.")
        return

    snd = parselmouth.Sound(y, sampling_frequency=sr)

    # 2. Syllable Nucleus
    seg = find_syllable_nucleus(snd)
    print(f"Syllable Nucleus: {seg}")

    if seg is None:
        print("!!! Could not find syllable nucleus (Voicing detection failed) !!!")
        # Retry with lower pitch floor?
        seg_retry = find_syllable_nucleus(snd, pitch_floor=50, pitch_ceiling=1200)
        print(f"Retry Nucleus (50Hz floor, 1200 ceil): {seg_retry}")
        # return # REMOVED EARLY RETURN TO TEST analyze_formants_from_path

    # 3. Formants
    # analyze_formants_from_path uses 5500 ceiling default
    meas, is_corrected = analyze_formants_from_path(path, vowel, is_reference=False)
    print(f"Measurements (F1, F2): {meas}")
    print(f"Deep Voice Corrected: {is_corrected}")

    # Check raw values
    points = (0.2, 0.8) if len(vowel) > 1 else (0.5,)  # heuristic from engine

    raw_meas = measure_formants(snd, seg, points, ceiling=5500.0)
    print(f"Raw Measure (5500Hz): {raw_meas}")

    # Diagnosis
    for i, (f1, f2) in enumerate(raw_meas):
        print(f"Point {i}: F1={f1}, F2={f2}")
        if np.isnan(f1):
            print("  -> F1 is NaN (filtered out? <50 or >1200?)")
        if np.isnan(f2):
            print("  -> F2 is NaN (filtered out? <200 or >4000?)")


if __name__ == "__main__":
    for item in TEST_CASES:
        debug_file(item)
