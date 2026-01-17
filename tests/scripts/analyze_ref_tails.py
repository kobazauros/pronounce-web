import sys
import os
import glob
import librosa
import numpy as np


def analyze_tails():
    audio_dir = r"static/audio"
    files = glob.glob(os.path.join(audio_dir, "*.mp3"))

    print(f"--- Analyzing {len(files)} Reference Files for Tail Duration ---")
    print(f"Threshold for Silence: 0.010 (RMS)")

    max_tail = 0
    worst_file = ""

    for f in files:
        y, sr = librosa.load(f, sr=16000, mono=True)
        duration = len(y) / sr

        frame_length = int(sr * 0.02)
        hop_length = frame_length
        rmse = librosa.feature.rms(
            y=y, frame_length=frame_length, hop_length=hop_length, center=False
        )[0]

        # Find last audible frame
        last_audible_idx = -1
        thresh = 0.010

        for i in range(len(rmse) - 1, -1, -1):
            if rmse[i] > thresh:
                last_audible_idx = i
                break

        if last_audible_idx == -1:
            print(f"{os.path.basename(f):10s}: SILENT FILE")
            continue

        # Find the "Peak" of the tail release (the last local max before silence)
        # Simplified: Just measure time from last "loud" frame (e.g. > 0.1) to last "audible" frame (> 0.01)
        # If the word ends abruptly, this diff is small. If it fades, it's large.

        # Let's define "Tail" as: Time from last sample > 0.05 (Voice) to last sample > 0.01 (Silence)
        # This represents the decay.

        voice_thresh = 0.05
        last_voice_idx = -1
        for i in range(len(rmse) - 1, -1, -1):
            if rmse[i] > voice_thresh:
                last_voice_idx = i
                break

        if last_voice_idx == -1:
            # Whole file is quiet?
            tail_duration = 0
        else:
            tail_diff_frames = last_audible_idx - last_voice_idx
            tail_duration = tail_diff_frames * 0.02

        if tail_duration > 0:
            print(f"{os.path.basename(f):10s}: {tail_duration:.3f}s")

        if tail_duration > max_tail:
            max_tail = tail_duration
            worst_file = os.path.basename(f)

    print("-" * 30)
    print(f"MAX TAIL DETECTED: {max_tail:.3f}s ({worst_file})")
    print(f"Current Padding:   0.300s")

    if max_tail < 0.250:
        print("✅ 300ms is SAFELY sufficient.")
    else:
        print("⚠️ WARNING: Tails approach padding limit.")


if __name__ == "__main__":
    analyze_tails()
