import librosa
import numpy as np
import pathlib

FILES = [
    "samples_new/hot/TopQuark_male_UK.mp3",
    "samples_new/ear/MichaelDS_male_UK.mp3",
    "samples_new/cup/eggypp_male_UK.mp3",
]

root = pathlib.Path(__file__).parent.parent

for f in FILES:
    path = root / f
    if path.exists():
        y, sr = librosa.load(path, sr=None)
        max_amp = np.max(np.abs(y))
        print(f"{f}: Max Amp = {max_amp:.4f}")
    else:
        print(f"{f}: Not Found")
