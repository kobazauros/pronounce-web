# pyright: strict
import io
from flask.testing import FlaskClient
from typing import List, Dict, Any, cast

# No pytest import needed if using fixtures via argument names matching conftest
from flask_app import db
from models import Submission, User, Word


def test_home_page_redirect_anonymous(client: FlaskClient):
    """Test that the home page redirects anonymous users to login."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_home_page_authenticated(auth_client: FlaskClient):
    """Test that the home page loads for authenticated users."""
    response = auth_client.get("/")
    assert response.status_code == 200
    assert b"Pronounce" in response.data


def test_login_page_loads(client: FlaskClient):
    """Test that the login page loads."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_get_progress_initial(auth_client: FlaskClient):
    """Test initial progress for a new student."""
    response = auth_client.get("/get_progress")
    assert response.status_code == 200
    data = cast(Dict[str, Any], response.get_json())
    assert data["stage"] == "pre"
    assert len(data["progress"]["pre"]) == 0


def test_process_audio_flow(auth_client: FlaskClient):
    """Test the audio processing endpoint."""
    data = {
        "audio": (io.BytesIO(b"RIFF....WAVEfmt...data..."), "test.wav"),
        "noiseFloor": 0.001,
    }

    response = auth_client.post(
        "/api/process_audio", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    json_data = cast(Dict[str, Any], response.get_json())
    assert json_data["status"] == "success"
    assert "path" in json_data


def test_get_progress_locked_post(auth_client: FlaskClient, curriculum: List[Word]):
    """Test that 20 pre-test words locks user into post-test."""
    user = cast(User | None, User.query.filter_by(username="teststudent").first())
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
    data = cast(Dict[str, Any], response.get_json())
    assert len(data["progress"]["pre"]) == 20
    assert data["stage"] == "post"
