import pytest
import sys
import os

# Ensure the app can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, db
from models import User, Word


@pytest.fixture
def client():
    """Configures the app for testing and returns a test client."""
    app.config["TESTING"] = True
    # Use a temporary file for the test database to ensure sharing between test and app
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{test_db_path}"
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for easier testing

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

    # Cleanup after tests
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def runner():
    """Returns a test runner for CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client):
    """Returns a client logged in as a test student."""
    user = User(username="teststudent", role="student", student_id="12345")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    client.post(
        "/login",
        data={"username": "teststudent", "password": "password"},
        follow_redirects=True,
    )

    return client


@pytest.fixture
def curriculum(client):
    """Populates the Word table with test data."""
    words = []
    for i in range(1, 26):  # Create 25 words for testing boundaries
        w = Word(
            text=f"word{i}", stressed_vowel="iː", audio_path=f"static/audio/word{i}.mp3"
        )
        words.append(w)
        db.session.add(w)
    db.session.commit()
    return words
