import sys
import os
import numpy as np
import librosa


def analyze_tail(file_path, label="Audio"):
    print(f"\n--- Analyzing {label}: {os.path.basename(file_path)} ---")
    y, sr = librosa.load(file_path, sr=16000, mono=True)
    duration = len(y) / sr

    frame_length = int(sr * 0.02)  # 20ms
    hop_length = frame_length

    rmse = librosa.feature.rms(
        y=y, frame_length=frame_length, hop_length=hop_length, center=False
    )[0]

    # Analyze last 500ms (25 frames)
    num_frames = len(rmse)
    lookback = min(25, num_frames)
    tail_rms = rmse[-lookback:]

    print(f"Total Duration: {duration:.3f}s")
    print(f"Tail Analysis (Last {lookback} frames = {lookback*0.02:.2f}s):")

    # 0.010 is our new aggressive threshold.
    # Let's see when it drops below that.
    thresh = 0.010
    dropout_idx = -1

    for i in range(len(tail_rms)):
        # checking from start of tail window
        val = tail_rms[i]
        # relative frame index from end
        rel_idx = i - lookback
        time_pos = duration + (rel_idx * 0.02)

        status = "LOUD" if val > thresh else "quiet"
        print(f"  {time_pos:.3f}s: {val:.5f} ({status})")

    # Calculate effective end (last time > thresh)
    # Scan whole file backwards
    effective_end = 0
    for i in range(len(rmse) - 1, -1, -1):
        if rmse[i] > thresh:
            effective_end = (i + 1) * 0.02
            break

    print(f"Effective End (Last audible > {thresh}): {effective_end:.3f}s")
    print(f"Silence at End: {duration - effective_end:.3f}s")


if __name__ == "__main__":
    user_file = r"submissions/2/c2cb55f9e61444449d59f279128464ec.mp3"
    # Word ID 4 is usually 'moon' or 'bird' -> check query output.
    # For now, I'll update the ref file dynamically if I can, but hardcoding 'bird.mp3' (guess) or waiting for query output is safer.
    # Let's just update the user file first.
    ref_file = r"static/audio/sheet.mp3"  # Placeholder, will confirm with query output

    if os.path.exists(user_file):
        analyze_tail(user_file, "User Recording")
    else:
        print(f"User file not found: {user_file}")

    if os.path.exists(ref_file):
        analyze_tail(ref_file, "Reference Audio")
    else:
        print(f"Ref file not found: {ref_file}")
