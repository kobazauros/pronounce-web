#!/usr/bin/env python3
"""
Thesis Vowel Analyzer 
"""

import argparse
import math
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from parselmouth.praat import call

import numpy as np
import pandas as pd
import librosa
import parselmouth

# --- CONFIGURATION ---
# Known Diphthongs in your dataset (IPA)
DIPHTHONGS = {"aɪ", "əʊ", "ɔɪ", "eɪ", "eə", "aʊ", "ɪə", "ʊə"}

def hz_to_bark(f: float) -> float:
    """Converts Hz to Bark scale."""
    if f is None or np.isnan(f) or f <= 0: return np.nan
    return 26.81 * f / (1960 + f) - 0.53

def get_vowel_type(vowel_symbol: str) -> str:
    """Decides if vowel is Monophthong or Diphthong based on symbol."""
    clean = vowel_symbol.replace("ː", "").replace("(", "").replace(")", "")
    if vowel_symbol in DIPHTHONGS or len(clean) > 1:
        return "diphthong"
    return "monophthong"

def load_audio_mono(path: Path, target_sr=16000) -> Tuple[np.ndarray, int]:
    """Loads audio, resamples to 16k, and normalizes volume."""
    try:
        y, sr = librosa.load(path.as_posix(), sr=None, mono=True)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return np.array([]), target_sr

    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    
    if y.size > 0:
        max_val = np.max(np.abs(y))
        if max_val > 0:
            y = 0.95 * y / max_val
    return y.astype(np.float32), int(sr)

def find_syllable_nucleus(sound: parselmouth.Sound, pitch_floor=75, pitch_ceiling=600):
    """Finds the loudest voiced segment (the vowel)."""
    pitch = sound.to_pitch(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    intensity = sound.to_intensity()
    
    n_frames = pitch.get_number_of_frames()
    voiced_intervals = []
    current_start: Optional[float] = None
    
    for i in range(1, n_frames + 1):
        if pitch.get_value_in_frame(i) > 0: 
            if current_start is None: 
                current_start = pitch.get_time_from_frame_number(i)
        else: 
            if current_start is not None:
                voiced_intervals.append((current_start, pitch.get_time_from_frame_number(i)))
                current_start = None
    if current_start: 
        voiced_intervals.append((current_start, pitch.get_time_from_frame_number(n_frames)))
    


    if not voiced_intervals: return None

    best_segment = None
    max_peak = -100.0
    
    for (t0, t1) in voiced_intervals:
        if (t1 - t0) < 0.03: continue
        try:
            peak = call(intensity, "Get maximum", float(t0), float(t1), "Parabolic")
            if peak > max_peak:
                max_peak = peak
                best_segment = (t0, t1)
        except: pass
            
    return best_segment

def measure_formants(sound, segment, points=(0.5,)) -> List[Tuple[float, float]]:
    """Measures F1/F2 at relative time points."""
    if segment is None:
        return [(np.nan, np.nan)] * len(points)
        
    t0, t1 = segment
    dur = t1 - t0
    formant = sound.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=5500.0)
    
    results = []
    for p in points:
        t = t0 + (dur * p)
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)
        


        if np.isnan(f1) or f1 < 50 or f1 > 1200: f1 = np.nan
        if np.isnan(f2) or f2 < 500 or f2 > 4000: f2 = np.nan
        
        results.append((f1, f2))
    return results

def analyze_single_file(filepath: Path, ref_dir: Path, word_map: Dict):
    # 1. Parse Filename: "ID_Name_Word.mp3"
    stem = filepath.stem 
    parts = stem.split('_')
    
    if len(parts) < 3:
        return None

    sid = parts[0]
    word = parts[-1].lower()
    name = " ".join(parts[1:-1])
    
    # 2. Determine Test Type (Folder Based)
    # Checks if 'pre' or 'post' exists in the parent folder names
    # e.g. "submissions/pre/file.mp3" -> "Pre-test"
    parent_folder = filepath.parent.name.lower()
    
    if "pre" in parent_folder:
        test_type = "Pre-test"
    elif "post" in parent_folder:
        test_type = "Post-test"
    else:
        # Fallback: Default to Pre-test if folder structure is ambiguous
        test_type = "Pre-test"
    
    # 3. Get Word Info
    info = word_map.get(word)
    if not info:
        print(f"Skipping unknown word: {word}")
        return None
        
    target_vowel = info.get("stressed_vowel", "?")
    v_type = get_vowel_type(target_vowel)
    
    # 4. Analyze Student Audio
    y_s, sr = load_audio_mono(filepath)
    if len(y_s) == 0: return None
    
    snd_s = parselmouth.Sound(y_s, sampling_frequency=sr)
    seg_s = find_syllable_nucleus(snd_s)
    
    points = (0.2, 0.8) if v_type == "diphthong" else (0.5,)
    meas_s = measure_formants(snd_s, seg_s, points)
    
    # 5. Analyze Reference Audio
    ref_path = ref_dir / f"{word}.mp3"
    meas_r = [(np.nan, np.nan)] * len(points)
    
    if ref_path.exists():
        y_r, _ = load_audio_mono(ref_path, target_sr=sr)
        if len(y_r) > 0:
            snd_r = parselmouth.Sound(y_r, sampling_frequency=sr)
            seg_r = find_syllable_nucleus(snd_r)
            meas_r = measure_formants(snd_r, seg_r, points)

    # 6. Calculate Distances
    hz_dists = []
    bark_dists = []
    
    f1_s_primary, f2_s_primary = meas_s[0]
    f1_r_primary, f2_r_primary = meas_r[0]

    for (f1s, f2s), (f1r, f2r) in zip(meas_s, meas_r):
        d_hz = math.hypot(f1s - f1r, f2s - f2r)
        hz_dists.append(d_hz)
        
        b1s, b2s = hz_to_bark(f1s), hz_to_bark(f2s)
        b1r, b2r = hz_to_bark(f1r), hz_to_bark(f2r)
        d_bark = math.hypot(b1s - b1r, b2s - b2r)
        bark_dists.append(d_bark)
    

        
    final_dist_hz = np.nanmean(hz_dists) if hz_dists else np.nan
    final_dist_bark = np.nanmean(bark_dists) if bark_dists else np.nan

    return {
        "student_ID": sid,
        "student_name": name,
        "word": word,
        "vowel": target_vowel,
        "vowel_type": v_type,
        "F1_student": f1_s_primary,
        "F2_student": f2_s_primary,
        "F1_ref": f1_r_primary,
        "F2_ref": f2_r_primary,
        "dist_hz": final_dist_hz,
        "dist_bark": final_dist_bark,
        "test_type": test_type,
        "ref_file_name": ref_path.name
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submissions", default="./submissions")
    ap.add_argument("--audio", default="./audio")
    ap.add_argument("--map", default="./audio/index.json")
    ap.add_argument("--out", default="./analysis_vowels")
    args = ap.parse_args()
    
    sub_dir, audio_dir, out_dir = Path(args.submissions), Path(args.audio), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    word_map = {}
    if Path(args.map).exists():
        with open(args.map, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data.get("words", []):
                w = entry.get("word", "").lower()
                word_map[w] = entry

    results = []
    print(f"Scanning {sub_dir} recursively...")
    
    # Use rglob to find files inside /pre and /post subfolders
    for f in sorted(sub_dir.rglob("*.mp3")):
        row = analyze_single_file(f, audio_dir, word_map)
        if row:
            results.append(row)
            print(f" Analyzed {f.name} ({row['test_type']}) -> Dist: {row['dist_hz']:.1f} Hz")
        else:
            print(f" Skipped {f.name} (Format error or unknown word)")

    df = pd.DataFrame(results)
    
    # Columns without timestamp
    cols = [
        "student_ID", "student_name", "word", "vowel", "vowel_type",
        "F1_student", "F2_student", "F1_ref", "F2_ref",
        "dist_hz", "dist_bark", "test_type", "ref_file_name"
    ]
    
    for c in cols:
        if c not in df.columns: df[c] = np.nan
            
    df = df[cols]
    
    out_csv = out_dir / "final_thesis_data.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nDone! Saved {len(df)} rows to {out_csv}")

if __name__ == "__main__":
    main()