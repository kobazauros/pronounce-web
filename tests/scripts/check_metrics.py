import numpy as np
import librosa


def compare_metrics():
    print("--- Metric Comparison: Peak vs RMS ---")
    sr = 16000
    duration = 1.0

    # 1. White Noise (Random)
    noise = np.random.uniform(-0.02, 0.02, int(sr * duration))

    peak = np.max(np.abs(noise))
    # RMS using Librosa defaults (frame_length 2048)
    rms_frames = librosa.feature.rms(
        y=noise, frame_length=320, hop_length=320, center=False
    )
    rms_avg = np.mean(rms_frames)

    print(f"Signal: White Noise (Max Amp 0.02)")
    print(f"  Peak:      {peak:.5f}")
    print(f"  RMS (Avg): {rms_avg:.5f}")
    print(f"  Ratio (RMS/Peak): {rms_avg/peak:.3f}")
    print("-" * 30)

    # 2. Sine Wave (Pure Tone)
    t = np.linspace(0, duration, int(sr * duration))
    sine = 0.02 * np.sin(2 * np.pi * 440 * t)

    peak_sine = np.max(np.abs(sine))
    rms_sine_frames = librosa.feature.rms(
        y=sine, frame_length=320, hop_length=320, center=False
    )
    rms_sine_avg = np.mean(rms_sine_frames)

    print(f"Signal: Sine Wave (Amp 0.02)")
    print(f"  Peak:      {peak_sine:.5f}")
    print(f"  RMS (Avg): {rms_sine_avg:.5f}")
    print(f"  Ratio (RMS/Peak): {rms_sine_avg/peak_sine:.3f} (Expected ~0.707)")


if __name__ == "__main__":
    compare_metrics()
