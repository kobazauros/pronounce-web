# pyright: strict
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
from flask_app import app
from models import Submission, Word


from typing import Any, Optional, Tuple, cast


def identify(filename: str) -> Tuple[Optional[str], Optional[str]]:
    with app.app_context():  # type: ignore
        # Search for submission with this filename
        # File path in DB is usually "user_id/filename"
        search_term = f"%{filename}"
        sub = cast(
            Submission | None,
            Submission.query.filter(
                cast(Any, Submission.file_path).like(search_term)
            ).first(),
        )

        if sub:
            word = cast(Word, sub.target_word)  # type: ignore
            print(f"--- Submission Found ---")
            print(f"ID: {sub.id}")
            print(f"User ID: {sub.user_id}")
            print(f"Word: {word.text}")
            print(f"Submission Path: {sub.file_path}")
            print(f"Reference Path: {word.audio_path}")
            return str(sub.file_path), str(word.audio_path)
        else:
            print(f"--- No Submission Found for {filename} ---")
            return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identify_submission.py <filename>")
        sys.exit(1)

    identify(sys.argv[1])
