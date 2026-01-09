import csv
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone

# Add parent directory to path so we can import app models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app
from models import AnalysisResult, Submission, User, Word, db

# Configuration
AUDIO_INDEX_PATH = os.path.join(app.config["AUDIO_FOLDER"], "index.json")
CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "analysis_vowels", "final_thesis_data.csv"
)
SOURCE_AUDIO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "submissions", "pre"
)

# ID Mapping to fix the discrepancy in Konstantin's CSV data
ID_CORRECTIONS = {"670120182": "6701202182"}


def seed_words():
    """Step 1: Populate Word table from index.json"""
    print(f"📖 Step 1: Seeding Words from {AUDIO_INDEX_PATH}")

    if not os.path.exists(AUDIO_INDEX_PATH):
        print(f"❌ Error: {AUDIO_INDEX_PATH} not found.")
        return

    with open(AUDIO_INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    words_list = data.get("words", []) if isinstance(data, dict) else data

    if not words_list:
        print("❌ Error: No words found in JSON.")
        return

    print(f"   🌱 Found {len(words_list)} words.")

    for i, item in enumerate(words_list, 1):
        text = item.get("word", item.get("text", "unknown")).lower()
        ipa = item.get("ipa", "")
        vowels_raw = item.get("vowels", item.get("vowel", ""))
        vowels = (
            ",".join(vowels_raw) if isinstance(vowels_raw, list) else str(vowels_raw)
        )
        stressed = item.get("stressed_vowel", item.get("stressed", ""))

        existing = Word.query.filter_by(text=text).first()
        if not existing:
            new_word = Word(
                text=text,
                sequence_order=i,
                ipa=ipa,
                vowels=vowels,
                stressed_vowel=stressed,
                audio_path=f"audio/{text}.mp3",
            )  # type: ignore
            db.session.add(new_word)

    db.session.commit()
    print("   ✅ Words seeded.")


def import_csv_data():
    """Step 2: Create Users & Analysis Records from CSV"""
    print(f"📊 Step 2: Importing Data from {CSV_PATH}")

    # Check for CSV in multiple locations
    csv_file = CSV_PATH
    if not os.path.exists(csv_file):
        alt_path = os.path.join(
            os.path.dirname(__file__), "..", "final_thesis_data.csv"
        )
        if os.path.exists(alt_path):
            csv_file = alt_path
        else:
            print("   ⚠️ CSV not found. Skipping CSV import.")
            return

    word_map = {w.text.lower(): w.id for w in Word.query.all()}

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            # 1. User with ID Correction
            raw_id = row.get("student_ID", row.get("ID", "unknown"))
            s_id = ID_CORRECTIONS.get(raw_id, raw_id)  # Apply Konstantin's ID fix

            full_name = row.get("student_name", row.get("name", "Student"))
            parts = full_name.split()
            first = parts[0] if parts else "Unknown"
            last = " ".join(parts[1:]) if len(parts) > 1 else "Student"

            user = User.query.filter_by(student_id=s_id).first()
            if not user:
                print(f"   👤 Registering: {full_name} ({s_id})")
                user = User(
                    username=s_id,
                    student_id=s_id,
                    first_name=first,
                    last_name=last,
                    role="student",
                    consented_at=datetime.now(timezone.utc),
                )  # type: ignore
                user.set_password("123456")
                db.session.add(user)
                db.session.commit()

            # 2. Submission
            word_text = row.get("word", "").lower()
            if word_text not in word_map:
                continue

            sub = Submission.query.filter_by(
                user_id=user.id, word_id=word_map[word_text]
            ).first()
            if not sub:
                temp_filename = f"{uuid.uuid4()}.mp3"
                sub = Submission(
                    user_id=user.id,
                    word_id=word_map[word_text],
                    test_type=row.get("test_type", "pre").lower(),
                    file_path=os.path.join(str(user.id), temp_filename).replace(
                        "\\", "/"
                    ),
                    timestamp=datetime.now(timezone.utc),
                    file_size_bytes=0,
                )  # type: ignore
                db.session.add(sub)
                db.session.commit()
                count += 1

            # 3. Analysis Result
            if not sub.analysis:

                def sf(k):
                    return float(row.get(k, 0) or 0)

                s_factor = sf("scaling_factor")
                d_bark = sf("dist_bark")

                # Logic for deep voice detection:
                # In your dataset, scaling_factor < 1.0 (e.g. 0.84) indicates the student's
                # frequencies were shifted UP (normalized > raw), typical for deep voices
                # compared to a higher-pitched reference.
                deep_voice = 0 < s_factor < 1.0

                # Logic for outlier detection:
                # Flag results with an extremely high perceptual distance (> 5.0 Bark)
                outlier = d_bark > 5.0

                res = AnalysisResult(
                    submission_id=sub.id,
                    f1_raw=sf("F1_student_raw"),
                    f2_raw=sf("F2_student_raw"),
                    f1_norm=sf("F1_student_norm"),
                    f2_norm=sf("F2_student_norm"),
                    f1_ref=sf("F1_ref"),
                    f2_ref=sf("F2_ref"),
                    distance_hz=sf("dist_hz"),
                    distance_bark=d_bark,
                    scaling_factor=s_factor,
                    is_deep_voice_corrected=deep_voice,
                    is_outlier=outlier,
                )  # type: ignore
                db.session.add(res)

        db.session.commit()
        print(f"   ✅ Imported {count} CSV records.")


def link_and_move_files():
    """Step 3: Scan legacy files, move to UUID path, and update DB"""
    print(f"📂 Step 3: Organizing Files from {SOURCE_AUDIO_DIR}")

    if not os.path.exists(SOURCE_AUDIO_DIR):
        print("   ⚠️ Source audio folder not found. Skipping file linking.")
        return

    files = [f for f in os.listdir(SOURCE_AUDIO_DIR) if f.lower().endswith(".mp3")]
    word_map = {w.text.lower(): w.id for w in Word.query.all()}

    updates = 0

    for filename in files:
        try:
            name_no_ext = os.path.splitext(filename)[0]
            parts = name_no_ext.split("_")
            if len(parts) < 4:
                continue

            raw_id = parts[0]
            s_id = ID_CORRECTIONS.get(
                raw_id, raw_id
            )  # Correct ID from filename if needed
            word_text = parts[3].lower()

            user = User.query.filter_by(student_id=s_id).first()
            if not user or word_text not in word_map:
                continue

            sub = Submission.query.filter_by(
                user_id=user.id, word_id=word_map[word_text]
            ).first()

            if not sub:
                new_uuid = uuid.uuid4()
                new_filename = f"{new_uuid}.mp3"
                sub = Submission(
                    user_id=user.id,
                    word_id=word_map[word_text],
                    test_type="pre",
                    file_path=os.path.join(str(user.id), new_filename).replace(
                        "\\", "/"
                    ),
                    timestamp=datetime.now(timezone.utc),
                    file_size_bytes=0,
                )  # type: ignore
                db.session.add(sub)
                db.session.commit()

            # File operation
            db_filename = os.path.basename(sub.file_path)
            dest_dir = os.path.join(app.config["UPLOAD_FOLDER"], str(user.id))
            os.makedirs(dest_dir, exist_ok=True)

            src = os.path.join(SOURCE_AUDIO_DIR, filename)
            dst = os.path.join(dest_dir, db_filename)

            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                sub.file_size_bytes = os.path.getsize(dst)
                updates += 1

        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")

    db.session.commit()
    print(f"   ✅ Linked {updates} files to UUID paths.")


if __name__ == "__main__":
    with app.app_context():
        # Force table creation if DB was deleted
        db.create_all()
        seed_words()
        import_csv_data()
        link_and_move_files()
        print("\n🎉 PHASE 0 COMPLETE: Data successfully migrated and linked.")
