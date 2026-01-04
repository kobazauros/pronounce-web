#!/usr/bin/env python3
"""
Thesis Vowel Analyzer (Monosyllable Edition)

Usage:
  python analyze_vowels.py --submissions ./submissions --audio ./audio --map ./audio/index.json
"""

import argparse
import math
import re
import json
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import librosa
import parselmouth
from parselmouth.praat import call

# Regex to handle: "67012 - bike - 20240101_120000.mp3" OR "67012 - bike.mp3"
# It grabs the FIRST part as ID and the SECOND part as Word. Ignores the rest.
FILENAME_RE = re.compile(r"^(?P<sid>.+?)\s*-\s*(?P<word>[^-.]+)(?:.*)?\.mp3$", re.IGNORECASE)

# Standard Monophthong Targets for reference (Hillenbrand male averages)
STANDARD_VOWELS = {
    "iː": {"F1": 270, "F2": 2290}, "ɪ":  {"F1": 390, "F2": 1990},
    "e":  {"F1": 530, "F2": 1840}, "æ":  {"F1": 660, "F2": 1720},
    "ɑː": {"F1": 730, "F2": 1090}, "ɔː": {"F1": 570, "F2": 840},
    "ʊ":  {"F1": 440, "F2": 1020}, "uː": {"F1": 300, "F2": 870},
    "ʌ":  {"F1": 640, "F2": 1190}, "ɜː": {"F1": 490, "F2": 1350},
    "ɒ":  {"F1": 600, "F2": 1000} 
}

def bark(f_hz: float) -> float:
    f = max(f_hz, 1e-6)
    return 26.81 * f / (1960 + f) - 0.53

def load_audio_mono(path: Path, target_sr=16000) -> Tuple[np.ndarray, int]:
    y, sr = librosa.load(path.as_posix(), sr=None, mono=True)
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr
    # Normalize volume
    if y.size > 0:
        y = 0.95 * y / np.max(np.abs(y))
    return y.astype(np.float32), int(sr)

def find_syllable_nucleus(sound: parselmouth.Sound, pitch_floor=75, pitch_ceiling=600):
    """
    Finds the 'Nucleus' (loudest voiced part) of the word.
    Returns (t_start, t_end) of that specific segment.
    """
    pitch = sound.to_pitch(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    intensity = sound.to_intensity()
    
    # 1. Find all voiced islands
    n_frames = pitch.get_number_of_frames()
    voiced_intervals = []
    current_start = None
    
    for i in range(1, n_frames + 1):
        if pitch.get_value_in_frame(i) > 0: # is voiced
            if current_start is None: 
                current_start = pitch.get_time_from_frame_number(i)
        else:
            if current_start is not None:
                voiced_intervals.append((current_start, pitch.get_time_from_frame_number(i)))
                current_start = None
    if current_start: 
        voiced_intervals.append((current_start, pitch.get_time_from_frame_number(n_frames)))

    if not voiced_intervals:
        return None

    # 2. Pick the Loudest Island (The Vowel Nucleus)
    best_segment = None
    max_peak = -100.0
    
    for (t0, t1) in voiced_intervals:
        # Check duration (ignore tiny noise < 30ms)
        if (t1 - t0) < 0.03: continue
        
        try:
            peak = intensity.get_maximum(t0, t1, "Parabolic")
            if peak > max_peak:
                max_peak = peak
                best_segment = (t0, t1)
        except: pass
            
    return best_segment

def measure_formants(sound, segment, points=(0.5,)):
    """
    Measures F1/F2 at specific relative points (e.g. 0.5 for center).
    Returns list of tuples: [(F1, F2), (F1, F2)...]
    """
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
        
        # Filter bad readings
        if np.isnan(f1) or f1 < 150 or f1 > 1200: f1 = np.nan
        if np.isnan(f2) or f2 < 500 or f2 > 4000: f2 = np.nan
        
        results.append((f1, f2))
    return results

def load_map_json(path: Path) -> dict:
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Map word -> info dict
    mapping = {}
    for entry in data.get("words", []):
        w = entry.get("word", "").lower().strip()
        if w: mapping[w] = entry
    return mapping

def analyze_file_pair(student_file, ref_file, word_info):
    # 1. Student Analysis
    y_s, sr = load_audio_mono(student_file)
    snd_s = parselmouth.Sound(y_s, sampling_frequency=sr)
    seg_s = find_syllable_nucleus(snd_s)
    
    # 2. Reference Analysis (if exists)
    snd_r, seg_r = None, None
    if ref_file and ref_file.exists():
        y_r, _ = load_audio_mono(ref_file, target_sr=sr)
        snd_r = parselmouth.Sound(y_r, sampling_frequency=sr)
        seg_r = find_syllable_nucleus(snd_r)
        
    # 3. Strategy: Monophthong vs Diphthong
    vowel_type = word_info.get("type", "monophthong")
    points = (0.2, 0.8) if vowel_type == "diphthong" else (0.5,)
    
    meas_s = measure_formants(snd_s, seg_s, points)
    meas_r = measure_formants(snd_r, seg_r, points) if snd_r else [(np.nan, np.nan)]*len(points)
    
    # 4. Calculate Distance
    # Average the distance of all points measured
    distances = []
    for (f1s, f2s), (f1r, f2r) in zip(meas_s, meas_r):
        dist = math.hypot(f1s - f1r, f2s - f2r)
        distances.append(dist)
        
    final_dist = np.mean(distances) if not np.isnan(distances).all() else np.nan
    
    # Return dominant formant (first point) for plotting
    return {
        "F1": meas_s[0][0],
        "F2": meas_s[0][1],
        "distance": final_dist,
        "type": vowel_type
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
    word_map = load_map_json(Path(args.map))
    
    results = []
    
    print(f"Scanning {sub_dir}...")
    for f in sorted(sub_dir.glob("*.mp3")):
        # Parse: "ID - Word - Timestamp.mp3"
        m = FILENAME_RE.match(f.name)
        if not m: continue
        
        sid = m.group("sid").strip()
        word = m.group("word").strip().lower()
        
        info = word_map.get(word, {})
        ref_path = audio_dir / f"{word}.mp3"
        
        res = analyze_file_pair(f, ref_path, info)
        
        results.append({
            "student_id": sid,
            "word": word,
            "vowel": info.get("target", "?"),
            "type": res["type"],
            "F1": res["F1"],
            "F2": res["F2"],
            "score_distance": res["distance"]
        })
        print(f" Analyzed {f.name} -> Dist: {res['distance']:.1f}")

    # Save
    df = pd.DataFrame(results)
    df.to_csv(out_dir / "final_thesis_data.csv", index=False)
    print(f"\nDone! Saved {len(df)} rows to {out_dir / 'final_thesis_data.csv'}")

if __name__ == "__main__":
    main()