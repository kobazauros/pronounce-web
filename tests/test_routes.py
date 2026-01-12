import io
import pytest
from flask_app import db
from models import Submission, User, Word


def test_home_page_redirect_anonymous(client):
    """Test that the home page redirects anonymous users to login."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_home_page_authenticated(auth_client):
    """Test that the home page loads for authenticated users."""
    response = auth_client.get("/")
    assert response.status_code == 200
    assert b"Pronounce" in response.data


def test_login_page_loads(client):
    """Test that the login page loads."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_get_progress_initial(auth_client):
    """Test initial progress for a new student."""
    response = auth_client.get("/get_progress")
    assert response.status_code == 200
    data = response.get_json()
    assert data["stage"] == "pre"
    assert data["counts"]["pre"] == 0


def test_upload_flow(auth_client, curriculum):
    """Test the full upload flow with a mock file."""
    data = {
        "audio": (io.BytesIO(b"RIFF....WAVEfmt...data..."), "test.wav"),
        "target_word": "word1",
        "test_type": "pre",
    }

    response = auth_client.post(
        "/upload", data=data, content_type="multipart/form-data"
    )
    assert response.status_code in [200, 500]

    sub = Submission.query.filter_by(test_type="pre").first()
    assert sub is not None
    assert sub.target_word.text == "word1"


def test_get_progress_locked_post(auth_client, curriculum):
    """Test that 20 pre-test words locks user into post-test."""
    user = User.query.filter_by(username="teststudent").first()
    assert user is not None, "Test user not found in database"
    user_id = user.id

    # Manually create 20 submissions for the test user
    for i in range(20):
        word = curriculum[i]
        sub = Submission(
            user_id=user_id, word_id=word.id, test_type="pre", file_path=f"test{i}.mp3"
        )
        db.session.add(sub)
    db.session.commit()

    response = auth_client.get("/get_progress")
    data = response.get_json()
    assert data["counts"]["pre"] == 20
    assert data["stage"] == "post"
