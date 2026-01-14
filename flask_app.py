import logging
import os
import uuid
import datetime
import json
import time
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
from models import Submission, SystemConfig, User, Word, db
from scripts.audio_processing import process_audio_data

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

# 2. Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)

# 3. Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # type: ignore
login_manager.login_message = "Please log to use this service."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Flask-Login requirement to reload the user object from the session ID."""
    return User.query.get(int(user_id))


# 4. Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboards, url_prefix="/dashboard")


# 5. Global Request Hook for Maintenance Mode
@app.before_request
def check_for_maintenance() -> Any:
    """
    Before any request, check if the site is in maintenance mode.
    If so, redirect to login or show a maintenance page.
    """
    from flask import redirect, url_for

    # Check if maintenance mode is enabled
    if SystemConfig.get_bool("maintenance_mode"):
        # Allow admins to access the site
        if current_user.is_authenticated and current_user.role == "admin":
            return None

        # Allow access to essential endpoints (auth, static files, config updates)
        if request.endpoint and request.endpoint.startswith(
            ("auth.", "static", "dashboards.update_config")
        ):
            return None

        # If user hits the root URL (/), redirect them to the login page.
        if request.endpoint == "index":
            return redirect(url_for("auth.login"))

        # For all other unauthorized endpoints, show the maintenance page.
        return render_template("maintenance.html"), 503


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
    words = Word.query.order_by(Word.sequence_order).all()  # type: ignore
    enable_logging = SystemConfig.get_bool("enable_logging", False)
    return render_template("index.html", words=words, enable_logging=enable_logging)


# 6a. API Route for Words (Replaces index.json)
@app.route("/api/words")
@login_required
def get_words_manifest() -> Response:
    """Returns the curriculum words as JSON for the frontend."""
    words = Word.query.order_by(Word.sequence_order).all()  # type: ignore
    return jsonify([{"word": w.text, "ipa": w.ipa} for w in words])


# 6b. Public About Page
@app.route("/about")
def about() -> str:
    """Renders the public About page."""
    return render_template("about.html")


@app.route("/manual")
def manual() -> str:
    """Renders the comprehensive User Manual."""
    return render_template("manual.html")


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

    # STRICT FLOW Enforcement (Backend)
    # Check if user is trying to submit 'post' while still in 'pre' stage
    if test_type == "post":
        # Calculate progress (Simplified logic from get_progress)
        # Count unique words submitted in 'pre' phase
        pre_submissions = (
            db.session.query(Submission.word_id)  # type: ignore
            .filter_by(user_id=current_user.id, test_type="pre")
            .distinct()
            .count()
        )
        if pre_submissions < 20:
            return (
                jsonify({"error": "Strict Flow: Complete Pre-Test (20 words) first."}),
                403,
            )

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

    # Save the physical file (Processed)
    try:
        file_bytes = file.read()
        processed_bytes = process_audio_data(file_bytes)

        with open(full_save_path, "wb") as f:
            f.write(processed_bytes)

    except ValueError as ve:
        # Known processing error (Clipping)
        app.logger.warning(f"Upload rejected: {ve}")
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        app.logger.error(f"Error saving file {unique_filename}: {e}")
        return jsonify({"error": "Failed to process and save audio file"}), 500

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
    )
    try:
        db.session.add(new_submission)
        db.session.commit()

        app.logger.info(
            f"User '{current_user.username}' uploaded file for word '{word.text}' ({test_type}-test). Path: {db_file_path}"
        )

        # Trigger Vowel Analysis (Phase 6 Real-time Engine)
        from analysis_engine import get_articulatory_feedback, process_submission

        analysis_success = process_submission(new_submission.id)
        if analysis_success:
            app.logger.info(f"Analysis completed for submission #{new_submission.id}")
        else:
            app.logger.warning(f"Analysis failed for submission #{new_submission.id}")

        # Prepare Response Data
        response_data = {
            "success": True,
            "submission_id": new_submission.id,
            "filename": unique_filename,
        }

        # Include basic analysis feedback if available
        if new_submission.analysis:
            res = new_submission.analysis

            # Generate Articulatory Recommendation (Only if score > 1.5 Bark)
            rec_text = None
            if res.distance_bark and res.distance_bark > 1.5:
                rec_text = get_articulatory_feedback(
                    res.f1_norm, res.f2_norm, res.f1_ref, res.f2_ref
                )

            response_data["analysis"] = {
                "distance_bark": (
                    round(res.distance_bark, 2) if res.distance_bark else None
                ),
                "is_outlier": res.is_outlier,
                "vowel": word.stressed_vowel,
                "recommendation": rec_text,
            }

        return jsonify(response_data), 200

    except Exception:
        db.session.rollback()
        # Cleanup file if DB save fails
        if os.path.exists(full_save_path):
            os.remove(full_save_path)
        return jsonify({"error": "Database error: could not save submission"}), 500


@app.route("/get_submission_audio/<path:filepath>")
@login_required
def get_submission_audio(filepath: str) -> Response:
    """Securely serves a submission audio file."""
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

    progress: dict[str, set[str]] = {"pre": set(), "post": set()}

    for s in subs:
        # Get the text of the word linked to this submission
        word = Word.query.get(s.word_id)
        if word and s.test_type in progress:
            progress[s.test_type].add(word.text)

    # Convert sets to lists for JSON serialization
    # Calculate Max Stage
    # STRICT FLOW:
    # If Pre Count < 20 -> Force 'pre'
    # If Pre Count >= 20 -> Force 'post'

    pre_count = len(progress["pre"])
    user_stage = "pre"
    if pre_count >= 20:  # Assuming 20 is the full curriculum
        user_stage = "post"

    return jsonify(
        {
            "progress": {k: list(v) for k, v in progress.items()},
            "stage": user_stage,
            "counts": {"pre": pre_count, "post": len(progress["post"])},
        }
    )


# 7a. Audio Processing Endpoint (Stateless Preview)
@app.route("/api/process_audio", methods=["POST"])
@login_required
def process_audio_preview() -> tuple[Response, int]:
    """
    Receives raw audio, processes it (trim/norm/convert),
    and returns the processed bytes for frontend preview.
    Does not save to DB or disk.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        raw_bytes = file.read()
        # Use our new robust trimming logic
        processed_bytes = process_audio_data(raw_bytes)

        return Response(processed_bytes, mimetype="audio/mpeg"), 200

    except Exception as e:
        app.logger.error(f"Preview processing failed: {e}")
        return jsonify({"error": "Processing failed"}), 500


# 7b. Logging Endpoint
@app.route("/api/log_event", methods=["POST"])
@login_required
def log_event() -> tuple[Response, int]:
    """Logs client-side events to a file."""
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    # Create logs directory if needed
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # File: session_<username>_<date>.jsonl
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"session_{current_user.username}_{date_str}.jsonl"
    filepath = os.path.join(log_dir, filename)

    try:
        # Add server timestamp if missing
        if "timestamp" not in data:
            data["timestamp"] = time.time()

        # Write JSON line
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

        return jsonify({"success": True}), 200
    except Exception as e:
        app.logger.error(f"Failed to log event: {e}")
        return jsonify({"error": "Logging failed"}), 500


# 8. CLI Commands
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username: str, password: str) -> None:
    """Create an admin user via CLI: flask create-admin <user> <pass>"""
    if User.query.filter_by(username=username).first():
        print(f"Error: User '{username}' already exists.")
        return

    user = User(username=username, first_name="System", last_name="Admin", role="admin")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Success: Admin user '{username}' created.")


@app.cli.command("delete-user")
@click.argument("username")
def delete_user(username: str) -> None:
    """Delete a user via CLI (including admins): flask delete-user <username>"""
    import shutil

    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"Error: User '{username}' not found.")
        return

    # Confirm deletion
    click.confirm(
        f"Are you sure you want to PERMANENTLY delete user '{username}' and all their data?",
        abort=True,
    )

    try:
        # Delete files
        user_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], str(user.id))
        if os.path.exists(user_upload_dir):
            shutil.rmtree(user_upload_dir)

        # Cascading DB delete (Submissions, InviteCodes used, etc need handling if not cascaded)
        # Assuming database cascade or manual cleanup.
        # Manual cleanup for safety as per dashboard_routes:
        Submission.query.filter_by(user_id=user.id).delete()

        # If they consumed an invite code, delete that usage record?
        # Actually in dashboard_routes we deleted the invite code itself if it was used by them?
        # "Cascade Delete: Remove associated InviteCode if this user used one".
        from models import InviteCode

        invite_used = InviteCode.query.filter_by(used_by_user_id=user.id).first()
        if invite_used:
            db.session.delete(invite_used)

        db.session.delete(user)
        db.session.commit()
        print(f"Success: User '{username}' deleted.")

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)
    app.run(debug=True)
