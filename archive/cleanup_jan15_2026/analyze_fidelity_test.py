import os
import sys
import logging
import numpy as np
import librosa
from pathlib import Path
from flask import Flask

# Setup path to import app (Must be done before imports)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from sqlalchemy.orm import joinedload
from models import db, User, Submission, Word

try:
    from flask_app import app
except ImportError:
    print("Error: Could not import flask_app. Run this from project root.")
    sys.exit(1)


def analyze_audio_file(filepath):
    """
    Analyzes a single audio file for leading/trailing silence and RMS energy.
    """
    try:
        y, sr = librosa.load(filepath, sr=16000, mono=True)
        if len(y) == 0:
            return None

        # RMS Energy
        rms = librosa.feature.rms(y=y, frame_length=320, hop_length=320)[0]
        max_rms = np.max(rms)
        mean_rms = np.mean(rms)

        # Silence Detection (Threshold: 1% of max volume or 0.001 absolute)
        threshold = max(0.001, max_rms * 0.01)

        # Find first/last sample above threshold
        above_thresh = np.where(np.abs(y) > threshold)[0]

        if len(above_thresh) == 0:
            return {
                "duration": 0,
                "leading_silence": 0,
                "trailing_silence": 0,
                "signal_detected": False,
            }

        first_sample = above_thresh[0]
        last_sample = above_thresh[-1]

        leading_ms = (first_sample / sr) * 1000
        trailing_ms = ((len(y) - last_sample) / sr) * 1000
        duration_ms = (len(y) / sr) * 1000

        return {
            "duration": duration_ms,
            "leading_silence": leading_ms,
            "trailing_silence": trailing_ms,
            "signal_detected": True,
            "max_amp": max_rms,
        }
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def main():
    with app.app_context():
        user = User.query.filter_by(username="test_fidelity").first()
        if not user:
            print("User 'test_fidelity' not found.")
            return

        submissions = (
            Submission.query.filter_by(user_id=user.id)
            .options(
                joinedload(Submission.target_word), joinedload(Submission.analysis)
            )
            .order_by(Submission.timestamp)
            .all()
        )

        if not submissions:
            print("No submissions found for test_fidelity.")
            return

    print(
        f"Found {len(submissions)} submissions. Writing report to analysis_results.md\n"
    )

    with open("analysis_results.md", "w", encoding="utf-8") as f:
        f.write("# Fidelity Test Analysis Report\n\n")
        f.write(f"**Found {len(submissions)} submissions.**\n\n")

        # Split into batches (assuming first 10 = Internal, next 10 = Headset)
        # Note: If user recorded 20 total, 0-9 is A, 10-19 is B.

        f.write(f"| ID | Word | End | Score (Bark) | Lead(ms) | Trail(ms) | Batch |\n")
        f.write(f"|---|---|---|---|---|---|---|\n")

        stats = {
            "Internal": {"k_trail": [], "t_trail": [], "other_trail": [], "scores": []},
            "Headset": {"k_trail": [], "t_trail": [], "other_trail": [], "scores": []},
        }

        for i, sub in enumerate(submissions):
            word = sub.target_word.text
            batch = "Internal" if i < 10 else "Headset"

            # Resolve file path
            # DB path: "user_id/uuid.mp3"
            # Real path: "uploads/user_id/uuid.mp3"
            real_path = os.path.join(app.config["UPLOAD_FOLDER"], sub.file_path)

            metrics = analyze_audio_file(real_path)

            if not metrics:
                f.write(f"| {sub.id} | {word} | ERROR | - | - | - | {batch} |\n")
                continue

            dist = sub.analysis.distance_bark if sub.analysis else 0.0

            # Determine Ending
            if word.lower().endswith("k") or word.lower().endswith("ke"):
                ending = "K"
                stats[batch]["k_trail"].append(metrics["trailing_silence"])
            elif word.lower().endswith("t") or word.lower().endswith("te"):
                ending = "T"
                stats[batch]["t_trail"].append(metrics["trailing_silence"])
            else:
                ending = "-"
                stats[batch]["other_trail"].append(metrics["trailing_silence"])

            stats[batch]["scores"].append(dist)

            f.write(
                f"| {sub.id} | {word} | {ending} | {dist:.2f} | {metrics['leading_silence']:.1f} | {metrics['trailing_silence']:.1f} | {batch} |\n"
            )

        f.write("\n## Summary Analysis\n")
        for batch in ["Internal", "Headset"]:
            s = stats[batch]
            f.write(f"\n### {batch} Mic\n")
            f.write(f"- Avg Score: **{np.mean(s['scores']):.2f} Bark**\n")
            f.write(
                f"- Avg Trailing Silence (K words): **{np.mean(s['k_trail']):.1f} ms**\n"
            )
            f.write(
                f"- Avg Trailing Silence (T words): **{np.mean(s['t_trail']):.1f} ms**\n"
            )

            k_t_diff = np.mean(s["t_trail"]) - np.mean(s["k_trail"])
            if k_t_diff > 50:
                f.write(
                    f"\n> ⚠️ **WARNING:** 'K' words result in {k_t_diff:.1f}ms LESS trailing silence than 'T' words.\n"
                )
                f.write("> **Evidence of premature cutoff for soft consonants.**\n")


if __name__ == "__main__":
    main()
