"""
Server-side Audio Analysis Engine
Ported from analyze_vowels.py for the Pronounce Web Application.
"""

import math
from pathlib import Path
from typing import List, Optional, Tuple, cast

import librosa
import numpy as np
import parselmouth
from parselmouth.praat import call  # pyright: ignore[reportMissingModuleSource]

# --- CONFIGURATION ---
DIPHTHONGS = {"aɪ", "əʊ", "ɔɪ", "eɪ", "eə", "aʊ", "ɪə", "ʊə"}
BACK_VOWELS = {"uː", "ʊ", "ɔː", "ɒ", "ɑː", "əʊ", "ɔɪ", "aʊ"}


def hz_to_bark(f: float) -> float:
    """Converts frequency (Hz) to Bark scale."""
    if np.isnan(f) or f <= 0:
        return np.nan
    return 26.81 * f / (1960 + f) - 0.53


def get_vowel_type(vowel_symbol: str) -> str:
    """Determines if a vowel is a monophthong or diphthong."""
    clean = vowel_symbol.replace("ː", "").replace("(", "").replace(")", "")
    if vowel_symbol in DIPHTHONGS or len(clean) > 1:
        return "diphthong"
    return "monophthong"


def load_audio_mono(path: Path | str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Loads audio, converts to mono, resamples to target_sr, and normalizes volume.
    """
    path_str = str(path)
    try:
        y: np.ndarray
        y, sr = librosa.load(path_str, sr=None, mono=True)
    except Exception as e:
        print(f"Error loading {path_str}: {e}")
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
) -> Optional[Tuple[float, float]]:
    """Finds the loudest voiced segment in the audio."""
    pitch = sound.to_pitch(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    intensity = sound.to_intensity()

    n_frames = pitch.get_number_of_frames()
    voiced_intervals: List[Tuple[float, float]] = []

    current_start: Optional[float] = None

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
    segment: Optional[Tuple[float, float]],
    points: Tuple[float, ...] = (0.5,),
    ceiling: float = 5500.0,
) -> List[Tuple[float, float]]:
    """
    Measures F1 and F2 at specified time points within the segment.
    """
    if segment is None:
        return [(np.nan, np.nan)] * len(points)

    t0, t1 = segment
    dur = t1 - t0

    formant = sound.to_formant_burg(
        time_step=0.01, max_number_of_formants=5, maximum_formant=ceiling
    )

    results: List[Tuple[float, float]] = []

    for p in points:
        t = t0 + (dur * p)
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)

        # Robust filtering
        if np.isnan(f1) or f1 < 50 or f1 > 1200:
            f1 = np.nan
        if np.isnan(f2) or f2 < 200 or f2 > 4000:
            f2 = np.nan

        results.append((f1, f2))
    return results


def analyze_formants_from_path(
    filepath: Path | str, target_vowel: str, is_reference: bool = False
) -> Tuple[List[Tuple[float, float]], bool]:
    """
    Analyzes an audio file and returns a list of (F1, F2) tuples and a boolean
    indicating if deep voice correction (4000Hz ceiling) was applied.
    """
    v_type = get_vowel_type(target_vowel)
    points = (0.2, 0.8) if v_type == "diphthong" else (0.5,)

    y, sr = load_audio_mono(filepath)
    if len(y) == 0:
        return [(np.nan, np.nan)] * len(points), False

    snd = parselmouth.Sound(y, sampling_frequency=sr)
    seg = find_syllable_nucleus(snd)

    # 1. Try Standard Ceiling (5500 Hz)
    meas = measure_formants(snd, seg, points, ceiling=5500.0)
    primary_f2 = meas[0][1]

    # 2. Retry if Deep Back Vowel detected
    # Thresholds: Student > 1500, Reference > 1600 (from original thesis logic)
    threshold = 1600 if is_reference else 1500

    is_corrected = False

    if target_vowel in BACK_VOWELS:
        if np.isnan(primary_f2) or primary_f2 > threshold:
            meas = measure_formants(snd, seg, points, ceiling=4000.0)
            is_corrected = True

    return meas, is_corrected


def get_articulatory_feedback(
    f1_norm: float, f2_norm: float, f1_ref: float, f2_ref: float
) -> str:
    """
    Generates articulatory instructions based on formant differences.
    """
    if np.isnan(f1_norm) or np.isnan(f2_norm):
        return ""

    feedback_parts = []

    # Thresholds (Hz)
    F1_THRESH = 50.0
    F2_THRESH = 100.0

    # F1 Analysis (Height/Jaw)
    # F1 is inversely related to tongue height / jaw closure
    f1_diff = f1_norm - f1_ref
    if f1_diff < -F1_THRESH:
        # F1 too low -> Tongue too high -> Open more
        feedback_parts.append("Open mouth more")
    elif f1_diff > F1_THRESH:
        # F1 too high -> Tongue too low -> Close slightly
        feedback_parts.append("Close mouth slightly")

    # F2 Analysis (Backness/Rounding)
    # F2 is directly related to frontness (high F2 = front)
    f2_diff = f2_norm - f2_ref
    if f2_diff < -F2_THRESH:
        # F2 too low -> Tongue too back -> Move forward
        feedback_parts.append("Move tongue forward")
    elif f2_diff > F2_THRESH:
        # F2 too high -> Tongue too front -> Move back
        feedback_parts.append("Move tongue back")

    if not feedback_parts:
        return ""

    return " & ".join(feedback_parts)


def calculate_distance(
    meas_s: List[Tuple[float, float]],
    meas_r: List[Tuple[float, float]],
    alpha: float = 1.0,
) -> Tuple[float, float]:
    """
    Calculates Euclidean distance in Hz and Bark between student and reference.
    Returns (dist_hz, dist_bark).
    """
    hz_dists: List[float] = []
    bark_dists: List[float] = []

    for (f1s, f2s), (f1r, f2r) in zip(meas_s, meas_r):
        # Normalize Student Formants
        f1s_norm = f1s / alpha
        f2s_norm = f2s / alpha

        # Hz Distance
        d_hz = math.hypot(f1s_norm - f1r, f2s_norm - f2r)
        hz_dists.append(d_hz)

        # Bark Distance
        b1s, b2s = hz_to_bark(f1s_norm), hz_to_bark(f2s_norm)
        b1r, b2r = hz_to_bark(f1r), hz_to_bark(f2r)
        d_bark = math.hypot(b1s - b1r, b2s - b2r)
        bark_dists.append(d_bark)

    avg_hz = float(np.nanmean(hz_dists)) if hz_dists else float("nan")
    avg_bark = float(np.nanmean(bark_dists)) if bark_dists else float("nan")

    return avg_hz, avg_bark


def process_submission(submission_id: int) -> bool:
    """
    Performs full acoustic analysis on a submission and saves the result to DB.
    Uses Cumulative VTLN (Median of all past + current ratios).
    """
    from flask import current_app

    from models import AnalysisResult, Submission, db

    try:
        # 1. Load Data
        sub = Submission.query.get(submission_id)
        if not sub:
            print(f"Submission {submission_id} not found.")
            return False

        user_id = sub.user_id
        word_text = sub.target_word.text.lower()
        target_vowel = sub.target_word.stressed_vowel

        # Resolve Paths
        # sub.file_path is relative (e.g., "1/uuid.mp3")
        # word.audio_path is relative (e.g., "word.mp3") - Check Model!
        # Actually Word model stores "static/audio/word.mp3" usually?
        # Let's assume standard location based on config if Word.audio_path is missing/unreliable
        student_path = Path(current_app.config["UPLOAD_FOLDER"]) / sub.file_path

        # Robust Reference Path Logic
        ref_filename = f"{word_text}.mp3"
        ref_path = Path(current_app.config["AUDIO_FOLDER"]) / ref_filename

        if not student_path.exists():
            print(f"Student file missing: {student_path}")
            return False
        if not ref_path.exists():
            print(f"Reference file missing: {ref_path}")
            # Ensure we don't crash, maybe log error?
            pass

        # 2. Analyze Current
        meas_s, is_deep_corrected = analyze_formants_from_path(
            student_path, target_vowel, is_reference=False
        )
        meas_r, _ = analyze_formants_from_path(
            ref_path, target_vowel, is_reference=True
        )

        f1s_raw, f2s_raw = meas_s[0]
        f1r, f2r = meas_r[0]

        # 3. Calculate Cumulative Alpha
        all_ratios = []

        # A) Get historical ratios from DB
        # Join Submission to filter by user_id
        history = (
            AnalysisResult.query.join(Submission)
            .filter(Submission.user_id == user_id)
            .all()
        )

        for h in history:
            if h.f1_raw and h.f1_ref and h.f1_ref > 0:
                all_ratios.append(h.f1_raw / h.f1_ref)
            if h.f2_raw and h.f2_ref and h.f2_ref > 0:
                all_ratios.append(h.f2_raw / h.f2_ref)

        # B) Add current ratios
        if not np.isnan(f1s_raw) and not np.isnan(f1r) and f1r > 0:
            all_ratios.append(f1s_raw / f1r)
        if not np.isnan(f2s_raw) and not np.isnan(f2r) and f2r > 0:
            all_ratios.append(f2s_raw / f2r)

        # C) Compute Median
        if all_ratios:
            alpha = float(np.median(all_ratios))
        else:
            alpha = 1.0

        # 4. Normalize & Score
        # Re-calc distance with this alpha
        dist_hz, dist_bark = calculate_distance(meas_s, meas_r, alpha)

        # Calculate specific normalized formants for storage
        f1_norm = f1s_raw / alpha if not np.isnan(f1s_raw) else np.nan
        f2_norm = f2s_raw / alpha if not np.isnan(f2s_raw) else np.nan

        # 5. Save Logic
        # Check if exists (idempotency)
        existing_result = AnalysisResult.query.filter_by(
            submission_id=submission_id
        ).first()
        if existing_result:
            result = existing_result
        else:
            result = AnalysisResult(submission_id=submission_id)

        result.f1_raw = f1s_raw
        result.f2_raw = f2s_raw
        result.f1_ref = f1r
        result.f2_ref = f2r
        result.scaling_factor = alpha
        result.f1_norm = f1_norm
        result.f2_norm = f2_norm
        result.distance_hz = dist_hz
        result.distance_bark = dist_bark

        # Diagnostic flags
        result.is_deep_voice_corrected = is_deep_corrected

        # Outlier Logic: Threshold > 5.0 Bark
        result.is_outlier = dist_bark > 5.0 if not np.isnan(dist_bark) else False

        if not existing_result:
            db.session.add(result)

        db.session.commit()
        print(
            f"Analysis saved for Sub {submission_id}. Alpha={alpha:.3f}, Dist={dist_bark:.2f} Bark"
        )
        return True

    except Exception as e:
        print(f"Analysis Failed: {e}")
        db.session.rollback()
        return False
