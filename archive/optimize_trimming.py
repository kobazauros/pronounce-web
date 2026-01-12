import csv
import librosa
import numpy as np
import os
import glob
from pathlib import Path

# --- Configuration ---
CSV_PATH = "Test recording - Sheet1.csv"
AUDIO_DIR = "submissions/10"
SR = 16000
FRAME_MS = 20
FRAME_SIZE = int(SR * FRAME_MS / 1000)


def load_ground_truth(csv_path):
    truth = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            truth[row["file_name"]] = {
                "start": float(row["sec_begin"]),
                "end": float(row["sec_end"]),
                "word": row["word"],
            }
    return truth


def simulate_trim(y, sr, vol_factor, sensitive_factor, zcr_thresh, noise_floor):
    """
    Simulates the JS trimSilence logic.
    """
    frame_size = int(sr * 0.02)  # 20ms
    n_frames = len(y) // frame_size

    vol_thresh = max(0.01, noise_floor * vol_factor)
    sensitive_thresh = max(0.002, noise_floor * sensitive_factor)

    start_frame = 0
    end_frame = n_frames - 1

    # Helper to calculate frame stats
    def is_speech(frame_idx):
        start = frame_idx * frame_size
        end = start + frame_size
        chunk = y[start:end]

        # JS Logic: sumSq += val*val, crosses...
        # Numpy equivalent
        rms = np.sqrt(np.mean(chunk**2))

        # ZCR: counts sign changes.
        # JS: if (i > 0 && (val > 0) !== (pcm[offset + i - 1] > 0)) crosses++;
        # Librosa ZCR is relative to frame length?
        # librosa.feature.zero_crossing_rate returns rate.
        # manually:
        zero_crossings = np.sum(np.abs(np.diff(np.signbit(chunk))))
        zcr = zero_crossings / frame_size

        return (rms > vol_thresh) or (rms > sensitive_thresh and zcr > zcr_thresh)

    while start_frame < n_frames and not is_speech(start_frame):
        start_frame += 1

    while end_frame > start_frame and not is_speech(end_frame):
        end_frame -= 1

    # JS adds 50ms padding
    padding_samples = int(sr * 0.05)

    start_time = max(0, (start_frame * frame_size - padding_samples) / sr)
    end_time = min(len(y) / sr, ((end_frame + 1) * frame_size + padding_samples) / sr)

    return start_time, end_time


def main():
    truth = load_ground_truth(CSV_PATH)
    files = list(truth.keys())

    # Measure "Noise Floor" for each file?
    # The JS logic measures it dynamically.
    # For optimization, we can assume the FIRST 100ms or so is noise?
    # Or rely on the fact that the files in submissions/10 might have started with some noise.
    # However, user's timestamps show start ~0.05s. This is very close to start.
    # The ACTUAL noise floor variable in JS `measuredNoiseFloor` adapts.
    # LOGS showed ~0.002 to ~0.02 range.
    # Let's try to estimate noise floor from the first 50ms of each file, or use a fixed representative value from logs (e.g. 0.005).
    # Better: Calculate it from the "Silence" parts defined by truth?
    # i.e. Noise = RMS of [0 : start] and [end : total]

    results = []

    # Grid Search Parameters
    # vol_factors = [1.5, 2.0, 2.5]
    # sensitive_factors = [1.1, 1.2, 1.3, 1.5]
    # zcr_thresholds = [0.05, 0.08, 0.1, 0.12, 0.15]

    # Simplified search for demonstration
    best_error = float("inf")
    best_params = None

    # Load all audio first to save time
    audio_cache = {}
    print("Loading audio...")
    for fname in files:
        path = os.path.join(AUDIO_DIR, fname)
        if os.path.exists(path):
            y, sr = librosa.load(path, sr=SR)
            # Normalize to -1..1 like JS? librosa does it.
            audio_cache[fname] = y

            # Estimate Noise Floor from silence regions
            t = truth[fname]
            start_samp = int(t["start"] * SR)
            end_samp = int(t["end"] * SR)

            noise_chunks = []
            if start_samp > 0:
                noise_chunks.append(y[:start_samp])
            if end_samp < len(y):
                noise_chunks.append(y[end_samp:])

            if noise_chunks:
                noise = np.concatenate(noise_chunks)
                truth[fname]["noise_floor"] = (
                    np.sqrt(np.mean(noise**2)) if len(noise) > 0 else 0.015
                )
            else:
                truth[fname]["noise_floor"] = 0.015
        else:
            print(f"Missing: {fname}")

    if not audio_cache:
        print("No audio files loaded. Check AUDIO_DIR and CSV path.")
        return

    print("\nOptimizing...")

    # Heuristic Search
    for vf in [1.5, 2.0, 3.0]:
        for sf in [1.1, 1.2, 1.5, 2.0]:
            for zcr in [0.05, 0.08, 0.1, 0.15, 0.2]:

                total_diff = 0
                max_diff = 0

                for fname, y in audio_cache.items():
                    nf = truth[fname]["noise_floor"]
                    # Use a smoothed/higher floor to be safe? JS logic uses "measuresNoiseFloor" which adapts.
                    # Let's use the Truth Noise Floor + 10% safety?
                    # Or just pass it raw.

                    s, e = simulate_trim(y, SR, vf, sf, zcr, nf)

                    # Error metric: How far is 'e' from truth['end']?
                    # We care mostly about NOT cutting too early (keeping tail) and NOT keeping too late.
                    # Truth end is tight.

                    diff = abs(e - truth[fname]["end"])
                    total_diff += diff
                    max_diff = max(max_diff, diff)

                avg_diff = total_diff / len(audio_cache)

                if avg_diff < best_error:
                    best_error = avg_diff
                    best_params = (vf, sf, zcr)
                    # print(f"New Best: Vol={vf}, Sens={sf}, ZCR={zcr} => AvgErr={avg_diff*1000:.1f}ms")

    print(f"\nOptimization Complete.")

    if best_params is None:
        print("Optimization failed to find parameters.")
        return

    print(f"Best Parameters:")
    print(f"  Vol Factor: {best_params[0]}")
    print(f"  Sens Factor: {best_params[1]}")
    print(f"  ZCR Thresh: {best_params[2]}")
    print(f"  Avg Error: {best_error*1000:.1f}ms")

    # Detailed report for best
    print("\nDetailed Comparison (Best Params):")
    vf, sf, zcr = best_params
    for fname, y in audio_cache.items():
        nf = truth[fname]["noise_floor"]
        s, e = simulate_trim(y, SR, vf, sf, zcr, nf)
        te = truth[fname]["end"]
        diff = e - te
        print(
            f"{truth[fname]['word']:<10} | Tru: {te:.3f} | Alg: {e:.3f} | Diff: {diff:+.3f}s | NF: {nf:.4f}"
        )


if __name__ == "__main__":
    main()
