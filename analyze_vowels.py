#!/usr/bin/env python3
"""
Vowel Analyzer (Praat/parselmouth)

Usage (from your project root):
  python analyze_vowels.py \
      --submissions ./submissions \
      --audio ./audio \
      --out ./analysis_vowels \
      [--map ./word_vowel_map.csv]
"""

import argparse
import math
import re
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import librosa
import parselmouth
from parselmouth.praat import call

FILENAME_RE = re.compile(r"^(?P<sid>.+?)\s*-\s*(?P<word>.+?)\.mp3$", re.IGNORECASE)

def bark(f_hz: float) -> float:
    """Traunmüller (1990) Bark scale."""
    f = max(f_hz, 1e-6)
    return 26.81 * f / (1960 + f) - 0.53

def load_audio_mono(path: Path, target_sr=16000) -> Tuple[np.ndarray, int]:
    y, sr = librosa.load(path.as_posix(), sr=None, mono=True)
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    if y.size > 0:
        y = 0.98 * y / np.max(np.abs(y))
    return y.astype(np.float32), sr

def trim_silence(y: np.ndarray, top_db=30.0) -> np.ndarray:
    if y.size == 0: return y
    yt, _ = librosa.effects.trim(y, top_db=top_db)
    return yt

def longest_voiced_segment(sound: parselmouth.Sound, pitch_floor=80, pitch_ceiling=400):
    """Return (t_start, t_end) of the longest contiguous voiced segment based on Praat Pitch."""
    pitch = call(sound, "To Pitch", 0.0, pitch_floor, pitch_ceiling)
    n = int(call(pitch, "Get number of frames"))
    if n <= 0:
        return None

    # frame times
    times = [call(pitch, "Get time from frame number", i+1) for i in range(n)]

    # voiced if pitch value (in Hertz) is finite and > 0
    voiced = []
    for i in range(n):
        val_hz = call(pitch, "Get value in frame", i+1, "Hertz")  # <-- add "Hertz"
        voiced.append(not (val_hz is None or np.isnan(val_hz) or val_hz <= 0))

    # find longest run of True
    best_len, best_range = 0, None
    i = 0
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]:
                j += 1
            if j - i > best_len:
                best_len = j - i
                best_range = (times[i], times[j-1])
            i = j
        else:
            i += 1
    return best_range


def f1_f2_at_midpoint(y: np.ndarray, sr: int, formant_ceiling=5500.0) -> Tuple[float, float]:
    """Estimate F1/F2 at vowel nucleus."""
    if y.size == 0:
        return float("nan"), float("nan")
    snd = parselmouth.Sound(y, sampling_frequency=sr)
    seg = longest_voiced_segment(snd)
    if seg is None: return float("nan"), float("nan")
    t0, t1 = seg
    t_mid = 0.5 * (t0 + t1)
    formant = call(snd, "To Formant (burg)", 0.0, 5, formant_ceiling, 0.025, 50)
    F1 = call(formant, "Get value at time", 1, t_mid, "Hertz", "Linear")
    F2 = call(formant, "Get value at time", 2, t_mid, "Hertz", "Linear")
    if not F1 or np.isnan(F1) or F1 < 150 or F1 > 1000: F1 = float("nan")
    if not F2 or np.isnan(F2) or F2 < 500 or F2 > 3500: F2 = float("nan")
    return F1, F2

def parse_filename(p: Path):
    m = FILENAME_RE.match(p.name)
    return (m.group("sid").strip(), m.group("word").strip()) if m else None

def load_map_csv(map_csv: Optional[Path]) -> dict:
    if not map_csv or not map_csv.exists(): return {}
    df = pd.read_csv(map_csv)
    return {str(row["word"]).strip(): str(row["vowel"]).strip() for _, row in df.iterrows()}

def analyze_pair(student_path: Path, ref_path: Path) -> dict:
    y_s, sr = load_audio_mono(student_path)
    y_s = trim_silence(y_s)
    y_r, sr_r = (np.array([], dtype=np.float32), sr)
    if ref_path.exists():
        y_r, sr_r = load_audio_mono(ref_path)
        y_r = trim_silence(y_r)
        if sr_r != sr:
            y_r = librosa.resample(y_r, orig_sr=sr_r, target_sr=sr)
    F1s, F2s = f1_f2_at_midpoint(y_s, sr)
    F1r, F2r = f1_f2_at_midpoint(y_r, sr) if y_r.size else (float("nan"), float("nan"))
    dist_hz = math.hypot(F1s-F1r, F2s-F2r) if not any(np.isnan([F1s,F2s,F1r,F2r])) else float("nan")
    dist_bark = math.hypot(bark(F1s)-bark(F1r), bark(F2s)-bark(F2r)) if not any(np.isnan([F1s,F2s,F1r,F2r])) else float("nan")
    return {"F1_student":F1s,"F2_student":F2s,"F1_ref":F1r,"F2_ref":F2r,
            "dist_hz":dist_hz,"dist_bark":dist_bark}

def scatter_vowel_space(df: pd.DataFrame, out_png: Path, title: str):
    plt.figure(figsize=(7,6))
    valid = df.dropna(subset=["F1_student","F2_student"])
    if valid.empty: return
    plt.scatter(valid["F2_student"], valid["F1_student"], label="Student")
    ref_valid = valid.dropna(subset=["F1_ref","F2_ref"])
    if not ref_valid.empty:
        plt.scatter(ref_valid["F2_ref"], ref_valid["F1_ref"], marker="x", label="Ref")
    plt.gca().invert_xaxis(); plt.gca().invert_yaxis()
    plt.xlabel("F2 (Hz)"); plt.ylabel("F1 (Hz)")
    plt.title(title); plt.legend(); plt.tight_layout()
    plt.savefig(out_png); plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions", type=str, default="./submissions")
    ap.add_argument("--audio", type=str, default="./audio")
    ap.add_argument("--out", type=str, default="./analysis_vowels")
    ap.add_argument("--map", type=str, default=None)
    args = ap.parse_args()

    subdir, refdir, outdir = Path(args.submissions), Path(args.audio), Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    word2vowel = load_map_csv(Path(args.map)) if args.map else {}

    rows = []
    for p in sorted(subdir.glob("*.mp3")):
        parsed = parse_filename(p)
        if not parsed: continue
        sid, word = parsed
        ref = refdir / f"{word}.mp3"
        res = analyze_pair(p, ref)
        res.update({"student_id":sid,"word":word,"vowel":word2vowel.get(word,"")})
        rows.append(res)

    df = pd.DataFrame(rows)
    df.to_csv(outdir/"results_vowels.csv", index=False)
    if not df.empty:
        agg = df.groupby("student_id").mean(numeric_only=True).reset_index()
        agg.to_csv(outdir/"per_student_summary_vowels.csv", index=False)
        if "vowel" in df.columns and df["vowel"].any():
            pv = df.groupby("vowel").mean(numeric_only=True).reset_index()
            pv.to_csv(outdir/"per_vowel_summary.csv", index=False)
        scatter_vowel_space(df, outdir/"vowel_space_overall.png", "Vowel Space")

if __name__ == "__main__":
    main()
