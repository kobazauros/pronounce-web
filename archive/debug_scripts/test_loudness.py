import os
import sys
import numpy as np
import librosa
import soundfile as sf
import parselmouth

# Add project root to path to import analysis_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis_engine import measure_formants, find_syllable_nucleus


def create_variants(input_path):
    print(f"Loading {input_path}...")
    y, sr = librosa.load(input_path, sr=16000, mono=True)

    variants = {}

    # 1. Normal (Normalized)
    max_val = np.max(np.abs(y))
    y_norm = 0.95 * y / max_val
    variants["Normal"] = y_norm

    # 2. Quiet (-20dB -> 0.1x amplitude)
    y_quiet = y_norm * 0.1
    variants["Quiet"] = y_quiet

    # 3. Clipped (+15dB -> ~5.6x, then clamped)
    # This simulates microphone preamp clipping
    gain = 5.6
    y_loud = y_norm * gain
    y_clipped = np.clip(y_loud, -1.0, 1.0)
    variants["Clipped"] = y_clipped

    return variants, sr


def analyze(name, y, sr):
    print(f"\nAnalyzing '{name}'...")
    snd = parselmouth.Sound(y, sampling_frequency=sr)

    # Get Intensity max to verify
    intensity = snd.to_intensity()
    max_int = intensity.get_maximum()
    print(f"  Max Intensity: {max_int:.2f} dB")

    seg = find_syllable_nucleus(snd)
    if not seg:
        print("  [!] No syllable nucleus found!")
        return None

    meas = measure_formants(snd, seg, points=(0.5,))
    f1, f2 = meas[0]

    print(f"  Result: F1={f1:.1f}, F2={f2:.1f}")
    return (f1, f2)


def main():
    target_file = "static/audio/moon.mp3"
    if not os.path.exists(target_file):
        print(f"Test file not found: {target_file}")
        return

    variants, sr = create_variants(target_file)

    results = {}

    for name, y in variants.items():
        results[name] = analyze(name, y, sr)

    # Compare
    ref = results["Normal"]
    if not ref:
        print("Normal analysis failed. Aborting.")
        return

    print("\n=== SUMMARY ===")
    print(f"{'Variant':<10} | {'F1':<8} | {'F2':<8} | {'Error %':<8}")
    print("-" * 45)

    for name, res in results.items():
        if not res or np.isnan(res[0]):
            print(f"{name:<10} | {'NaN':<8} | {'NaN':<8} | {'FAIL':<8}")
            continue

        f1, f2 = res
        # Euclidean Error in Hz
        dist = np.sqrt((f1 - ref[0]) ** 2 + (f2 - ref[1]) ** 2)
        ref_mag = np.sqrt(ref[0] ** 2 + ref[1] ** 2)
        err_pct = (dist / ref_mag) * 100

        print(f"{name:<10} | {f1:<8.1f} | {f2:<8.1f} | {err_pct:<8.1f}%")


if __name__ == "__main__":
    main()
