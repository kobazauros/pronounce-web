import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from typing import Any

import click
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate

from auth_routes import auth
from config import Config
from dashboard_routes import dashboards
from models import Submission, User, Word, db

# 1. Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# --- Logging Setup ---
# This runs only in production-like environments (not in debug mode)
if not app.debug and not app.testing:
    # Create a logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # Use a rotating file handler to keep log files from getting too large
    file_handler = RotatingFileHandler(
        "logs/pronounce.log", maxBytes=10240, backupCount=10
    )

    # Set the log format for detailed, readable logs
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Pronounce application startup")

# 2. Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)

# 3. Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # type: ignore
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Flask-Login requirement to reload the user object from the session ID."""
    return User.query.get(int(user_id))


# 4. Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboards, url_prefix="/dashboard")


# 5. Shell Context for Debugging
@app.shell_context_processor
def make_shell_context() -> dict[str, Any]:
    from models import AnalysisResult

    return {
        "db": db,
        "User": User,
        "Word": Word,
        "Submission": Submission,
        "AnalysisResult": AnalysisResult,
    }


# 6. Main Application Route
@app.route("/")
@login_required
def index() -> str:
    """Renders the main student recording interface."""
    words = Word.query.order_by(Word.sequence_order).all()
    return render_template("index.html", words=words)


# 6a. API Route for Words (Replaces index.json)
@app.route("/api/words")
@login_required
def get_words_manifest() -> Response:
    """Returns the curriculum words as JSON for the frontend."""
    words = Word.query.order_by(Word.sequence_order).all()
    return jsonify([{"word": w.text, "ipa": w.ipa} for w in words])


# 7. File Upload Route (Updated for Phase 3 DB Integration)
@app.route("/upload", methods=["POST"])
@login_required
def upload_file() -> tuple[Response, int]:
    """
    Handles audio submission:
    1. Saves physical file with a unique UUID.
    2. Creates a Submission record in the database.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    word_text = request.form.get("word")
    test_type = request.form.get("testType", "pre")

    if file.filename == "" or not word_text:
        return jsonify({"error": "Missing file or word context"}), 400

    # Type narrowing: word_text is now str (not None)
    # 1. Find the Word object in the database to get the word_id
    word = Word.query.filter_by(text=word_text.lower()).first()
    if not word:
        return jsonify({"error": "Selected word not found in curriculum"}), 404

    # 2. Setup user folder
    user_folder = os.path.join(app.config["UPLOAD_FOLDER"], str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    # 3. Generate unique UUID filename (Anonymized)
    unique_filename = f"{uuid.uuid4()}.mp3"
    full_save_path = os.path.join(user_folder, unique_filename)

    # Save the physical file
    file.save(full_save_path)

    # 4. Create and Save the Submission record
    # The path stored in DB should be relative to the UPLOAD_FOLDER, using forward slashes
    db_file_path = os.path.join(str(current_user.id), unique_filename).replace(
        "\\", "/"
    )

    new_submission = Submission(
        user_id=current_user.id,
        word_id=word.id,
        test_type=test_type,
        # Relative path stored for portability
        file_path=db_file_path,
        file_size_bytes=os.path.getsize(full_save_path),
    )  # type: ignore
    try:
        db.session.add(new_submission)
        db.session.commit()

        app.logger.info(
            f"User '{current_user.username}' uploaded file for word '{word.text}' ({test_type}-test). Path: {db_file_path}"
        )
        # Note: In Phase 4, we will trigger vowel analysis here
        return jsonify(
            {
                "success": True,
                "submission_id": new_submission.id,
                "filename": unique_filename,
            }
        ), 200

    except Exception:
        db.session.rollback()
        # Cleanup file if DB save fails
        if os.path.exists(full_save_path):
            os.remove(full_save_path)
        return jsonify({"error": "Database error: could not save submission"}), 500


@app.route("/get_submission_audio/<path:filepath>")
@login_required
def get_submission_audio(filepath: str) -> Response:
    """Securely serves a submission audio file."""  # type: ignore
    # Security check: only teachers or admins should access this.
    if current_user.role not in ["teacher", "admin"]:
        return Response("Access Denied", status=403)

    # Sanitize path for legacy data: if it starts with 'submissions/', remove it.
    # This handles old data ('submissions/1/file.wav') and new data ('1/file.wav').
    if filepath.startswith("submissions/"):
        filepath = filepath.partition("/")[-1]

    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filepath, as_attachment=False
    )


@app.route("/get_progress")
@login_required
def get_progress() -> Response:
    """Returns a JSON object of words the current user has already submitted."""
    from models import Submission

    # Fetch all submissions for current user
    subs = Submission.query.filter_by(user_id=current_user.id).all()

    progress: dict[str, list[str]] = {"pre": [], "post": []}

    for s in subs:
        # Get the text of the word linked to this submission
        word = Word.query.get(s.word_id)
        if word and s.test_type in progress:
            progress[s.test_type].append(word.text)

    return jsonify(progress)


# 8. CLI Commands
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Create an admin user via CLI: flask create-admin <user> <pass>"""
    if User.query.filter_by(username=username).first():
        print(f"Error: User '{username}' already exists.")
        return

    user = User(username=username, first_name="System", last_name="Admin", role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Success: Admin user '{username}' created.")


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)
    app.run(debug=True)
