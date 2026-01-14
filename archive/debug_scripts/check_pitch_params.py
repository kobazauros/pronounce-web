import sys
import os
import pathlib
import parselmouth
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis_engine import load_audio_mono

FILE_PATH = "samples_new/cat/MichaelDS_male_UK.mp3"


def check_params():
    path = pathlib.Path(__file__).parent.parent / FILE_PATH
    y, sr = load_audio_mono(path)
    snd = parselmouth.Sound(y, sampling_frequency=sr)

    # Test 1200
    p1 = snd.to_pitch(pitch_floor=75.0, pitch_ceiling=1200.0)
    vals1 = p1.selected_array["frequency"]
    frames = np.where(vals1 > 0)[0]
    print(f"Ceiling 1200: {len(frames)} frames. Indices: {frames}")

    # Test 1000
    p2 = snd.to_pitch(pitch_floor=75.0, pitch_ceiling=1000.0)
    vals2 = p2.selected_array["frequency"]
    print(f"Ceiling 1000: {len(vals2[vals2>0])} frames")

    # Test 850
    p3 = snd.to_pitch(pitch_floor=75.0, pitch_ceiling=850.0)
    vals3 = p3.selected_array["frequency"]
    print(f"Ceiling 850: {len(vals3[vals3>0])} frames")


if __name__ == "__main__":
    check_params()
