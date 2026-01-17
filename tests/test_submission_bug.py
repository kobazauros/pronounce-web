# pyright: strict
from flask import json, Flask
from flask.testing import FlaskClient
from typing import cast
from models import Submission, Word, db

# Removed unused User import


def test_submit_recording_preserves_test_type(auth_client: FlaskClient, app: Flask):
    """
    Regression Test: Ensure that when a recording is submitted with test_type='post',
    it is saved correctly in the database, instead of defaulting to 'pre'.
    """
    # 1. Setup: Ensure we have a word and user
    with app.app_context():
        # Ensure a word exists
        word = cast(Word | None, Word.query.first())
        if not word:
            word = Word(text="testword", sequence_order=1, ipa="test", vowels="e")
            db.session.add(word)
            db.session.commit()

        word_id = word.id

    # 2. Simulate submission with test_type='post'
    data = {
        "word_id": word_id,
        "file_path": "dummy/path.mp3",
        "test_type": "post",  # This was previously ignored
    }

    response = auth_client.post(
        "/api/submit_recording", data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == 200

    # 3. Verify in Database
    with app.app_context():
        # Get the latest submission
        submission = cast(
            Submission | None, Submission.query.order_by(Submission.id.desc()).first()
        )

        assert submission is not None
        assert (
            submission.test_type == "post"
        ), f"Expected 'post', but got '{submission.test_type}'"
