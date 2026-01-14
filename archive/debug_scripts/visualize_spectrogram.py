import os
import pathlib
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

# Configuration
FILES = [
    {
        "path": "samples_new/cat/MichaelDS_male_UK.mp3",
        "title": "MichaelDS (Cat) - High Pitch (Visible Harmonics)",
        "out": "spectrogram_michaelds.png",
    },
    {
        "path": "samples_new/hot/TopQuark_male_UK.mp3",
        "title": "TopQuark (Hot) - Whisper (Noise, No Harmonics)",
        "out": "spectrogram_topquark.png",
    },
]

ARTIFACTS_DIR = pathlib.Path(
    r"C:\Users\rookie\.gemini\antigravity\brain\e343fc0d-7734-4d1f-86d4-18e2e32abbb5"
)
ROOT_DIR = pathlib.Path(__file__).parent.parent


def generate_spectrograms():
    for item in FILES:
        path = ROOT_DIR / item["path"]
        if not path.exists():
            print(f"Missing: {path}")
            continue

        y, sr = librosa.load(path, sr=None)

        plt.figure(figsize=(10, 4))
        D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)

        # Plot up to 4000Hz (relevant for speech)
        librosa.display.specshow(D, sr=sr, x_axis="time", y_axis="hz")
        plt.ylim(0, 8000)
        plt.colorbar(format="%+2.0f dB")
        plt.title(item["title"])
        plt.tight_layout()

        out_path = ARTIFACTS_DIR / item["out"]
        plt.savefig(out_path)
        print(f"Saved: {out_path}")
        plt.close()


if __name__ == "__main__":
    generate_spectrograms()
