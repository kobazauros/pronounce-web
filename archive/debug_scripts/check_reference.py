import sys
import os
import pathlib
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis_engine import analyze_formants_from_path

REF_PATH = "static/audio/cat.mp3"
VOWEL = "æ"


def check_ref():
    path = pathlib.Path(__file__).parent.parent / REF_PATH
    print(f"\n=== Analyzing Reference {path.name} ===")

    if not path.exists():
        print("File not found")
        return

    meas, is_corrected = analyze_formants_from_path(str(path), VOWEL, is_reference=True)
    print(f"Measurements: {meas}")

    if np.isnan(meas[0][0]):
        print("!!! REFERENCE FAILED ANALYSIS !!!")


if __name__ == "__main__":
    check_ref()
