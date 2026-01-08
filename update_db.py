import os
import sys

# Add parent directory to path so we can import app models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app
from models import Word, db


def update_paths():
    with app.app_context():
        words = Word.query.all()
        print(words)
        count = 0
        for word in words:
            # Change 'audio/word.mp3' to 'static/audio/word.mp3'
            if word.audio_path and not word.audio_path.startswith("static/"):
                word.audio_path = f"static/{word.audio_path}"
                count += 1

        db.session.commit()
        print(f"✅ Successfully updated {count} word paths in the database.")


if __name__ == "__main__":
    update_paths()
