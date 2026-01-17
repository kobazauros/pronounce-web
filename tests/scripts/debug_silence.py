import sys
import os
import numpy as np
import librosa
import soundfile as sf
import io

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.audio_processing import process_audio_data


def debug_trim(file_path):
    print(f"--- Debugging File: {os.path.basename(file_path)} ---")

    # 1. Load Original
    y, sr = librosa.load(file_path, sr=16000, mono=True)
    print(f"Original Duration: {len(y)/sr:.3f}s ({len(y)} samples)")

    # --- COPY OF LOGIC FROM audio_processing.py FOR INSPECTION ---
    frame_length = int(sr * 0.02)  # 320 samples
    hop_length = frame_length

    rmse = librosa.feature.rms(
        y=y, frame_length=frame_length, hop_length=hop_length, center=False
    )[0]
    zcr = librosa.feature.zero_crossing_rate(
        y=y, frame_length=frame_length, hop_length=hop_length, center=False
    )[0]

    # Adaptive Threshold Calculation
    sorted_rms = np.sort(rmse)
    floor_idx = int(len(sorted_rms) * 0.1)
    local_floor = sorted_rms[floor_idx] if floor_idx < len(sorted_rms) else 0.001
    local_floor = max(0.001, local_floor)

    vol_thresh = max(0.015, local_floor * 2.0)

    print(f"\n--- Metrics ---")
    print(f"Calculated Noise Floor (10th percentile): {local_floor:.5f}")
    print(f"Volume Threshold (2.0x floor):            {vol_thresh:.5f}")
    print(f"Min Volume Threshold (Hardcoded):         0.01500")
    print(f"Active Threshold (used):                  {vol_thresh:.5f}")

    print(f"\n--- Frame Analysis (First 20 frames = 0.4s) ---")
    print(f"Frame | RMSE    | > Thresh? | ZCR")
    for i in range(min(50, len(rmse))):
        is_loud = rmse[i] > vol_thresh
        mark = "*" if is_loud else " "
        print(f"{i:3d}   | {rmse[i]:.5f} | {mark}         | {zcr[i]:.3f}")

    print(f"\n--- Trimming Result ---")
    # Actually run the function to see what it returns
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    processed_bytes = process_audio_data(raw_bytes, target_sr=16000)

    # Decode processed
    y_proc, sr_proc = librosa.load(io.BytesIO(processed_bytes), sr=16000)
    print(f"Processed Duration: {len(y_proc)/sr_proc:.3f}s")
    print(f"Removed: {len(y)/sr - len(y_proc)/sr_proc:.3f}s")


if __name__ == "__main__":
    target_file = r"c:\Users\rookie\Documents\Projects\pronounce-web\7982be4e74214290a6293da90b121e26.mp3"
    debug_trim(target_file)
