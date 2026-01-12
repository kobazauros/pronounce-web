import sys
import os
import time

# Add parent directory to path so we can import app models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app
from models import Submission, db
from analysis_engine import process_submission


def reprocess_all():
    """
    Iterates through all submissions and re-runs process_submission.
    This effectively backfills new analysis columns (deep voice, outlier)
    and updates VTLN factors.
    """
    with app.app_context():
        submissions = Submission.query.order_by(Submission.id).all()
        count = len(submissions)
        print(f"🚀 Starting reprocessing of {count} submissions...")

        success_count = 0
        error_count = 0

        start_time = time.time()

        for i, sub in enumerate(submissions, 1):
            print(
                f"[{i}/{count}] Processing Sub #{sub.id} (User {sub.user_id}, Word {sub.target_word.text})...",
                end="",
                flush=True,
            )

            try:
                # We commit inside process_submission, but let's be safe
                if process_submission(sub.id):
                    print(" ✅ Done")
                    success_count += 1
                else:
                    print(" ❌ Failed")
                    error_count += 1
            except Exception as e:
                print(f" 💥 Error: {e}")
                error_count += 1

        elapsed = time.time() - start_time
        print("\n" + "=" * 50)
        print(f"🏁 Reprocessing Complete in {elapsed:.2f}s")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed:    {error_count}")
        print("=" * 50)


if __name__ == "__main__":
    reprocess_all()
