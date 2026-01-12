import librosa
import numpy as np
import sys
import glob
import os


def analyze_file(path):
    print(f"Analyzing {path}...")
    try:
        y, sr = librosa.load(path, sr=None)

        # Calculate trailing silence manually to see dB levels
        # Frame size for RMS
        frame_length = 2048
        hop_length = 512

        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
        rms_db = librosa.power_to_db(rms[0], ref=np.max)

        # Check last frames
        print(f"Total Duration: {librosa.get_duration(y=y, sr=sr):.3f}s")
        print(f"Peak Amplitude: {np.max(np.abs(y)):.4f}")

        # Librosa trim suggestion with different thresholds
        for top_db in [30, 40, 50, 60]:
            yt, index = librosa.effects.trim(y, top_db=top_db)
            start_time = index[0] / sr
            end_time = index[1] / sr
            trimmed_duration = librosa.get_duration(y=yt, sr=sr)
            print(f"--- Trim (top_db={top_db}) ---")
            print(f"  Trimmed Interval: {start_time:.3f}s to {end_time:.3f}s")
            print(f"  New Duration: {trimmed_duration:.3f}s")
            print(
                f"  Removed: {librosa.get_duration(y=y, sr=sr) - trimmed_duration:.3f}s"
            )

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    audio_dir = r"c:\Users\rookie\Documents\Projects\pronounce-web\static\audio"
    files = glob.glob(os.path.join(audio_dir, "*.mp3"))

    with open("silence_report.log", "w", encoding="utf-8") as log_file:
        original_stdout = sys.stdout
        sys.stdout = log_file
        try:
            print(f"Found {len(files)} files.")
            for f in files:
                analyze_file(f)
                print("-" * 40)
        finally:
            sys.stdout = original_stdout

    print("Analysis complete. Check silence_report.log")
