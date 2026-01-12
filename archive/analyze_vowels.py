#!/usr/bin/env python3
"""
Thesis Vowel Analyzer (Adaptive Reference + VTLN)
"""

import argparse
import json
import math
from pathlib import Path
from typing import TypedDict, cast

import librosa
import numpy as np
import pandas as pd
import parselmouth
from parselmouth.praat import call  # pyright: ignore[reportMissingModuleSource]

# --- CONFIGURATION ---
DIPHTHONGS = {"aɪ", "əʊ", "ɔɪ", "eɪ", "eə", "aʊ", "ɪə", "ʊə"}
# These vowels often have low F2 that merges with F1 in deep voices
BACK_VOWELS = {"uː", "ʊ", "ɔː", "ɒ", "ɑː", "əʊ", "ɔɪ", "aʊ"}


class RawAnalysisResult(TypedDict):
    student_ID: str
    student_name: str
    word: str
    vowel: str
    vowel_type: str
    test_type: str
    meas_s: list[tuple[float, float]]
    meas_r: list[tuple[float, float]]
    ref_file_name: str


class FinalAnalysisResult(TypedDict):
    student_ID: str
    student_name: str
    word: str
    vowel: str
    vowel_type: str
    test_type: str
    scaling_factor: float
    F1_student_raw: float
    F2_student_raw: float
    F1_student_norm: float
    F2_student_norm: float
    F1_ref: float
    F2_ref: float
    dist_hz: float
    dist_bark: float
    ref_file_name: str


class WordInfo(TypedDict, total=False):
    word: str
    ipa: str
    vowels: list[str]
    stressed_vowel: str


class StudentData(TypedDict):
    ratios: list[float]
    alpha: float


def hz_to_bark(f: float) -> float:
    if np.isnan(f) or f <= 0:
        return np.nan
    return 26.81 * f / (1960 + f) - 0.53


def get_vowel_type(vowel_symbol: str) -> str:
    clean = vowel_symbol.replace("ː", "").replace("(", "").replace(")", "")
    if vowel_symbol in DIPHTHONGS or len(clean) > 1:
        return "diphthong"
    return "monophthong"


def load_audio_mono(path: Path, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    try:
        y: np.ndarray
        y, sr = librosa.load(path.as_posix(), sr=None, mono=True)

    except Exception as e:
        print(f"Error loading {path}: {e}")
        return np.array([]), target_sr

    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    if y.size > 0:
        max_val: float = float(cast(float, np.max(np.abs(y))))
        if max_val > 0:
            y = 0.95 * y / max_val
    return y.astype(np.float32), int(sr)


def find_syllable_nucleus(
    sound: parselmouth.Sound, pitch_floor: float = 75, pitch_ceiling: float = 600
) -> tuple[float, float] | None:
    """Finds the loudest voiced segment."""
    pitch = sound.to_pitch(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    intensity = sound.to_intensity()

    n_frames = pitch.get_number_of_frames()
    voiced_intervals: list[tuple[float, float]] = []

    current_start: float | None = None

    for i in range(1, n_frames + 1):
        if pitch.get_value_in_frame(i) > 0:
            if current_start is None:
                current_start = pitch.get_time_from_frame_number(i)
        else:
            if current_start is not None:
                voiced_intervals.append(
                    (current_start, pitch.get_time_from_frame_number(i))
                )
                current_start = None
    if current_start:
        voiced_intervals.append(
            (current_start, pitch.get_time_from_frame_number(n_frames))
        )

    if not voiced_intervals:
        return None

    best_segment = None
    max_peak = -100.0

    for t0, t1 in voiced_intervals:
        if (t1 - t0) < 0.03:
            continue
        try:
            peak: float = float(
                cast(
                    float,
                    call(intensity, "Get maximum", float(t0), float(t1), "Parabolic"),
                )
            )
            if peak > max_peak:
                max_peak = peak
                best_segment = (t0, t1)
        except:
            pass

    return best_segment


def measure_formants(
    sound: parselmouth.Sound,
    segment: tuple[float, float] | None,
    points: tuple[float, ...] = (0.5,),
    ceiling: float = 5500.0,
) -> list[tuple[float, float]]:
    if segment is None:
        return [(np.nan, np.nan)] * len(points)

    t0, t1 = segment
    dur = t1 - t0

    # Use the requested ceiling (Standard=5500, Deep=4000)
    formant = sound.to_formant_burg(
        time_step=0.01, max_number_of_formants=5, maximum_formant=ceiling
    )

    results: list[tuple[float, float]] = []

    for p in points:
        t = t0 + (dur * p)
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)

        # Robust filtering:
        # F2 < 200 is extremely rare, but for deep 'moon' it might be 300-400.
        if np.isnan(f1) or f1 < 50 or f1 > 1200:
            f1 = np.nan
        if np.isnan(f2) or f2 < 200 or f2 > 4000:
            f2 = np.nan

        results.append((f1, f2))
    return results


def analyze_raw_data(
    filepath: Path, ref_dir: Path, word_map: dict[str, "WordInfo"]
) -> RawAnalysisResult | None:
    """Pass 1: Collect raw formants with Adaptive Logic."""
    stem = filepath.stem
    parts = stem.split("_")
    if len(parts) < 3:
        return None

    sid = parts[0]
    word = parts[-1].lower()
    name = " ".join(parts[1:-1])

    parent_folder = filepath.parent.name.lower()
    if "pre" in parent_folder:
        test_type = "Pre-test"
    elif "post" in parent_folder:
        test_type = "Post-test"
    else:
        test_type = "Pre-test"

    info: WordInfo | None = word_map.get(word)

    if not info:
        return None

    target_vowel: str = str(info.get("stressed_vowel", "?"))

    v_type = get_vowel_type(target_vowel)
    points = (0.2, 0.8) if v_type == "diphthong" else (0.5,)

    # --- STUDENT ANALYSIS ---
    y_s, sr = load_audio_mono(filepath)
    if len(y_s) == 0:
        return None
    snd_s = parselmouth.Sound(y_s, sampling_frequency=sr)

    seg_s = find_syllable_nucleus(snd_s)

    # 1. Try Standard (5500)
    meas_s = measure_formants(snd_s, seg_s, points, ceiling=5500.0)
    primary_f2_s = meas_s[0][1]

    # 2. Retry if Deep Back Vowel detected (F2 missing or suspiciously high)
    if target_vowel in BACK_VOWELS:
        if np.isnan(primary_f2_s) or primary_f2_s > 1500:
            meas_s = measure_formants(snd_s, seg_s, points, ceiling=4000.0)

    # --- REFERENCE ANALYSIS ---
    ref_path = ref_dir / f"{word}.mp3"
    meas_r = [(np.nan, np.nan)] * len(points)

    if ref_path.exists():
        y_r, _ = load_audio_mono(ref_path, target_sr=sr)
        if len(y_r) > 0:
            snd_r = parselmouth.Sound(y_r, sampling_frequency=sr)
            seg_r = find_syllable_nucleus(snd_r)

            # 1. Try Standard (5500)
            meas_r = measure_formants(snd_r, seg_r, points, ceiling=5500.0)
            primary_f2_r = meas_r[0][1]

            # 2. REFERENCE RETRY (This fixes "Moon")
            # If Ref F2 is > 1600 for a back vowel, it's definitely F3. Retry deeper.
            if target_vowel in BACK_VOWELS:
                if np.isnan(primary_f2_r) or primary_f2_r > 1600:
                    # Retry with 4000 ceiling to force finding the real F2 (~800-900)
                    meas_r = measure_formants(snd_r, seg_r, points, ceiling=4000.0)

    return {
        "student_ID": sid,
        "student_name": name,
        "word": word,
        "vowel": target_vowel,
        "vowel_type": v_type,
        "test_type": test_type,
        "meas_s": meas_s,
        "meas_r": meas_r,
        "ref_file_name": ref_path.name,
    }


def main():
    ap = argparse.ArgumentParser()
    _ = ap.add_argument("--submissions", default="./submissions")
    _ = ap.add_argument("--audio", default="./audio")
    _ = ap.add_argument("--map", default="./audio/index.json")
    _ = ap.add_argument("--out", default="./analysis_vowels")

    args = ap.parse_args()

    sub_dir = Path(cast(str, args.submissions))
    audio_dir = Path(cast(str, args.audio))
    out_dir = Path(cast(str, args.out))

    out_dir.mkdir(parents=True, exist_ok=True)

    word_map: dict[str, WordInfo] = {}

    if Path(cast(str, args.map)).exists():
        with open(cast(str, args.map), "r", encoding="utf-8") as f:
            data = cast(dict[str, object], json.load(f))

            # Cast effectively handles the Any from json.load for strict typed dict usage
            for entry in cast(list[WordInfo], data.get("words", [])):
                w = str(entry.get("word", "")).lower()

                word_map[w] = entry

    # --- PASS 1: COLLECT RAW DATA ---
    print(f"Phase 1: Scanning files in {sub_dir}...")
    raw_results: list[RawAnalysisResult] = []

    for f in sorted(sub_dir.rglob("*.mp3")):
        row = analyze_raw_data(f, audio_dir, word_map)
        if row:
            raw_results.append(row)
            print(f"  Read {f.name}")
        else:
            print(f"  Skipped {f.name}")

    # --- PASS 2: CALCULATE SCALING FACTORS (VTLN) ---
    print("\nPhase 2: Calculating Normalization Factors...")

    students: dict[str, StudentData] = {}

    for r in raw_results:
        sid = r["student_ID"]
        if sid not in students:
            students[sid] = StudentData(ratios=[], alpha=1.0)

        f1s, f2s = r["meas_s"][0]
        f1r, f2r = r["meas_r"][0]

        if not np.isnan(f1s) and not np.isnan(f1r):
            students[sid]["ratios"].append(f1s / f1r)
        if not np.isnan(f2s) and not np.isnan(f2r):
            students[sid]["ratios"].append(f2s / f2r)

    for sid, s_data in students.items():
        if s_data["ratios"]:
            alpha = float(np.median(s_data["ratios"]))

            s_data["alpha"] = alpha
        else:
            s_data["alpha"] = 1.0
        print(f"  Student {sid}: Scaling Factor = {s_data['alpha']:.3f}")

    # --- PASS 3: APPLY NORMALIZATION & SAVE ---
    print("\nPhase 3: Finalizing Data...")
    final_rows: list[FinalAnalysisResult] = []

    for r in raw_results:
        sid = r["student_ID"]
        alpha = students[sid]["alpha"]

        hz_dists: list[float] = []
        bark_dists: list[float] = []
        meas_s_norm: list[tuple[float, float]] = []

        for (f1s, f2s), (f1r, f2r) in zip(r["meas_s"], r["meas_r"]):
            # Normalize Student Formants (Divide by scaling factor)
            f1s_norm = f1s / alpha
            f2s_norm = f2s / alpha
            meas_s_norm.append((f1s_norm, f2s_norm))

            d_hz = math.hypot(f1s_norm - f1r, f2s_norm - f2r)
            hz_dists.append(d_hz)

            b1s, b2s = hz_to_bark(f1s_norm), hz_to_bark(f2s_norm)
            b1r, b2r = hz_to_bark(f1r), hz_to_bark(f2r)
            d_bark = math.hypot(b1s - b1r, b2s - b2r)
            bark_dists.append(d_bark)

        # Construct safe explicit TypedDict
        f_row: FinalAnalysisResult = {
            "student_ID": r["student_ID"],
            "student_name": r["student_name"],
            "word": r["word"],
            "vowel": r["vowel"],
            "vowel_type": r["vowel_type"],
            "test_type": r["test_type"],
            "scaling_factor": alpha,
            "F1_student_raw": r["meas_s"][0][0],
            "F2_student_raw": r["meas_s"][0][1],
            "F1_student_norm": meas_s_norm[0][0],
            "F2_student_norm": meas_s_norm[0][1],
            "F1_ref": r["meas_r"][0][0],
            "F2_ref": r["meas_r"][0][1],
            "dist_hz": float(np.nanmean(hz_dists)) if hz_dists else float("nan"),
            "dist_bark": float(np.nanmean(bark_dists)) if bark_dists else float("nan"),
            "ref_file_name": r["ref_file_name"],
        }

        final_rows.append(f_row)

    df: pd.DataFrame = pd.DataFrame(final_rows)

    cols = [
        "student_ID",
        "student_name",
        "word",
        "vowel",
        "vowel_type",
        "test_type",
        "scaling_factor",
        "F1_student_raw",
        "F2_student_raw",
        "F1_student_norm",
        "F2_student_norm",
        "F1_ref",
        "F2_ref",
        "dist_hz",
        "dist_bark",
        "ref_file_name",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan

    df = df[cols]  # type: ignore [assignment]

    out_csv = out_dir / "final_thesis_data.csv"
    df.to_csv(out_csv, index=False)
    print(f"Done! Saved {len(df)} rows to {out_csv}")


if __name__ == "__main__":
    main()
