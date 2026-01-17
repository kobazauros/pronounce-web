# pyright: strict
import sys
import os

# Add parent directory to path to import flask_app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask_app import app, db, User, Word, Submission

from typing import List, cast


def seed_graduated_user():
    username = "student_graduated"
    password = "password"

    print(f"Seeding user: {username}")

    # 1. Create/Get User
    user = cast(User | None, User.query.filter_by(username=username).first())
    if not user:
        user = User(
            username=username,
            first_name="Graduated",
            last_name="Student",
            student_id="GRAD001",
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("User created.")
    else:
        print("User already exists.")

    # 2. Get all 20 words
    words = cast(List[Word], Word.query.order_by(Word.sequence_order).limit(20).all())  # type: ignore
    if len(words) < 20:
        print("WARNING: Less than 20 words in DB. Completing all available.")

    # 3. Create 'pre' submissions for all words
    # Remove existing to ensure clean slate
    Submission.query.filter_by(user_id=user.id, test_type="pre").delete()
    db.session.commit()

    print("Creating submissions...")
    for w in words:
        sub = Submission(
            user_id=user.id,
            word_id=w.id,
            test_type="pre",
            file_path=f"dummy/{w.text}.mp3",  # Dummy path
            file_size_bytes=1024,
        )
        db.session.add(sub)

    db.session.commit()
    print(f"Success! {len(words)} 'pre' submissions created for {username}.")


if __name__ == "__main__":
    with app.app_context():
        seed_graduated_user()
