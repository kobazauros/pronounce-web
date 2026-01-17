import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from flask_app import app, db
from models import Submission, Word


def identify(filename):
    with app.app_context():
        # Search for submission with this filename
        # File path in DB is usually "user_id/filename"
        search_term = f"%{filename}"
        sub = Submission.query.filter(Submission.file_path.like(search_term)).first()

        if sub:
            word = sub.target_word
            print(f"--- Submission Found ---")
            print(f"ID: {sub.id}")
            print(f"User ID: {sub.user_id}")
            print(f"Word: {word.text}")
            print(f"Submission Path: {sub.file_path}")
            print(f"Reference Path: {word.audio_path}")
            return sub.file_path, word.audio_path
        else:
            print(f"--- No Submission Found for {filename} ---")
            return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identify_submission.py <filename>")
        sys.exit(1)

    identify(sys.argv[1])
