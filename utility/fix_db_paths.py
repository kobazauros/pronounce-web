import os
import sys

# Add parent directory to path so we can import app models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, db
from models import Submission


def fix_submission_paths():
    """
    Scans all submissions in the database and normalizes their file_path attribute.
    This script corrects two common issues:
    1. Replaces Windows-style backslashes (`\\`) with forward slashes (`/`).
    2. Removes the legacy `submissions/` prefix from the path.

    Example: `submissions\\1\\file.mp3` -> `1/file.mp3`
    """
    with app.app_context():
        all_submissions = Submission.query.all()

        if not all_submissions:
            print("No submissions found in the database.")
            return

        print(f"Scanning {len(all_submissions)} submissions for path normalization...")
        updated_count = 0

        for sub in all_submissions:
            original_path = sub.file_path
            # 1. Normalize backslashes to forward slashes
            normalized_path = original_path.replace("\\", "/")

            # 2. Remove leading 'submissions/' if it exists
            if normalized_path.startswith("submissions/"):
                normalized_path = normalized_path.partition("/")[-1]

            # If the path was changed, update the record
            if normalized_path != original_path:
                print(f"  - Updating path for submission {sub.id}:")
                print(f"    - From: {original_path}")
                print(f"    - To:   {normalized_path}")
                sub.file_path = normalized_path
                updated_count += 1

        if updated_count > 0:
            print(f"\nFound {updated_count} paths to update. Committing changes...")
            db.session.commit()
            print("✅ Database updated successfully.")
        else:
            print("✅ All submission paths are already in the correct format.")


if __name__ == "__main__":
    print("--- Starting Submission Path Fixer ---")
    fix_submission_paths()
    print("--- Process Finished ---")
