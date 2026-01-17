import logging
import os
import uuid
import datetime
import json
import time
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

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
# --- Sentry Integration (Production Observability) ---
try:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.flask import FlaskIntegration  # type: ignore
except ImportError:
    sentry_sdk = None

if sentry_sdk and os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
        profiles_sample_rate=1.0,  # Profile 100% of sampled transactions
    )

app = Flask(__name__)
app.config.from_object(Config)

# --- Celery Setup ---
from celery import Celery, Task


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(
        app.config["CELERY_CONFIG"] if "CELERY_CONFIG" in app.config else app.config
    )
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


celery = celery_init_app(app)

# Import tasks to ensure they are registered with the Celery worker
import tasks

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


# 6. Routes


@app.route("/")
def index() -> str | Response:
    """
    Home Page / Dashboard.
    Redirects to login if not authenticated.
    """
    if current_user.is_authenticated:
        return render_template(
            "index.html",
            user=current_user,
            enable_logging=SystemConfig.get_bool("enable_logging"),
        )
    return render_template("login.html")


@app.route("/about")
def about() -> str:
    """About Page."""
    return render_template("about.html")


@app.route("/manual")
def manual() -> str:
    """User Manual Page."""
    return render_template("manual.html")


@app.route("/admin/init")
def init_metrics() -> Response | tuple[Response, int]:
    """
    Hidden endpoint to initialize the word list.
    Only allows running if the word table is empty.
    """
    # Security: Only allow if no words exist or user is admin
    if Word.query.count() > 0 and (
        not current_user.is_authenticated or current_user.role != "admin"
    ):
        return (
            jsonify({"status": "error", "message": "Database already initialized"}),
            403,
        )

    from scripts.parser import update_word_list

    added = update_word_list(limit=20)
    return jsonify({"status": "success", "added": added})


@app.route("/api/log_event", methods=["POST"])
@login_required
def log_event() -> Response | tuple[Response, int]:
    """
    Accepts analytics events from the frontend.
    Events are logged for debugging and user behavior analysis.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    event_type = data.get("event")
    timestamp = data.get("timestamp")

    # Log to application logger for debugging
    app.logger.info(f"Event: {event_type} | User: {current_user.id} | Data: {data}")

    # Future: Store in database for analytics
    # EventLog.create(user_id=current_user.id, event_type=event_type, data=data)

    return jsonify({"status": "success"})


@app.route("/api/word_list")
@login_required
def get_word_list() -> Response | tuple[Response, int]:
    """
    API to fetch words for the frontend list.
    Supports filtering by active/inactive.
    """
    # In the future, we can add phase logic here (Pre-test vs Post-test)
    words = Word.query.order_by(Word.sequence_order).all()  # type: ignore[arg-type]
    # Serialize
    data = [
        {"id": w.id, "word": w.text, "ipa": w.ipa, "audio": w.audio_path} for w in words
    ]
    return jsonify(data)


@app.route("/get_progress")
@login_required
def get_progress():
    """Returns user progress for strict stage enforcement."""
    # Query submissions by test_type (not phase)
    pre_subs = Submission.query.filter_by(
        user_id=current_user.id, test_type="pre"
    ).all()
    post_subs = Submission.query.filter_by(
        user_id=current_user.id, test_type="post"
    ).all()

    # Get word text from the relationship
    pre_words = [s.target_word.text for s in pre_subs]
    post_words = [s.target_word.text for s in post_subs]

    # Simple logic: if pre is full, stage is post.
    # We know there are 20 words.
    stage = "post" if len(pre_words) >= 20 else "pre"

    return jsonify({"progress": {"pre": pre_words, "post": post_words}, "stage": stage})


@app.route("/api/process_audio", methods=["POST"])
@login_required
def api_process_audio() -> Response | tuple[Response, int]:
    """
    Receives raw audio blob, processes it (trim/normalize), and saves it.
    Input: Multipart form data with 'audio' file.
    Output: JSON with 'url' of processed file.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["audio"]
    # Get client noise floor if provided
    noise_floor: Optional[float] = request.form.get("noiseFloor", type=float)

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read raw bytes
        raw_data = file.read()

        # Process (Trim, Normalize, Convert to MP3)
        processed_data = process_audio_data(
            raw_data, noise_floor=noise_floor if noise_floor is not None else 0.0
        )

        # Generate specific filename for this upload
        # Structure: uploads/<user_id>/<uuid>.mp3
        user_upload_dir = os.path.join(
            app.config["UPLOAD_FOLDER"], str(current_user.id)
        )
        os.makedirs(user_upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(user_upload_dir, filename)

        # Save to disk
        with open(filepath, "wb") as f:
            f.write(processed_data)

        # Return URL accessible via static route (or custom route)
        # We need a route to serve these if they are outside 'static'
        # Assuming UPLOAD_FOLDER is mapped or we serve via endpoint
        # Let's return a relative path that the frontend can use with a serving endpoint
        relative_path = f"{current_user.id}/{filename}"

        return jsonify(
            {
                "status": "success",
                "path": relative_path,
                # Return a preview URL if we have a route for it
                "url": f"/uploads/{relative_path}",
            }
        )

    except Exception as e:
        app.logger.error(f"Audio Processing Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename: str) -> Response:
    """Serves user uploaded files."""
    # Ensure security! verify user has access?
    # For now, simplistic serving.
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/api/submit_recording", methods=["POST"])
@login_required
def submit_recording() -> Response | tuple[Response, int]:
    """
    Analyzes the user's recording against the reference model.
    """
    data = request.json
    if notData := (not data):  # Walrus operator for "if not data"
        return jsonify({"error": "No data"}), 400

    word_id = data.get("word_id")
    file_path = data.get("file_path")  # Relative path returned by process_audio

    if not word_id or not file_path:
        return jsonify({"error": "Missing word_id or file_path"}), 400

    word = Word.query.get(word_id)
    if not word:
        return jsonify({"error": "Word not found"}), 404

    # 1. Create Submission Record
    test_type = data.get("test_type", "pre")  # Default to 'pre' if not provided

    sub = Submission(
        user_id=current_user.id,
        word_id=word.id,
        file_path=file_path,
        test_type=test_type,
        # Score will be updated after analysis
    )
    db.session.add(sub)
    db.session.commit()

    # 2. Trigger Analysis Engine (ASYNC)
    # Use send_task to avoid circular imports and type checker issues
    task = celery.send_task("tasks.async_process_submission", args=[sub.id])

    return jsonify({"status": "processing", "task_id": task.id}), 202

    return jsonify({"status": "error", "message": "Analysis failed"}), 500


@app.route("/api/status/<task_id>")
@login_required
def get_task_status(task_id):
    """
    Poll this endpoint to check if the analysis is done.
    """
    from celery.result import AsyncResult

    task_result = AsyncResult(task_id)

    if task_result.state == "PENDING":
        return jsonify({"status": "processing"})
    elif task_result.state == "SUCCESS":
        return jsonify(
            task_result.result
        )  # Returns the dict {status: success, score: ...}
    elif task_result.state == "FAILURE":
        return jsonify({"status": "error", "message": str(task_result.result)}), 500
    else:
        return jsonify({"status": "processing"})

    # Ensure default config exists
    if not SystemConfig.get("maintenance_mode"):
        SystemConfig.set("maintenance_mode", "False")

    db.session.commit()
    print("Initialized the database with default config.")


@app.cli.command("process-submission")
@click.argument("submission_id")
def process_submission_cmd(submission_id):
    """Manually trigger analysis for a submission."""
    from analysis_engine import process_submission

    if process_submission(int(submission_id)):
        print(f"Successfully processed submission {submission_id}")
    else:
        print(f"Failed to process submission {submission_id}")


@app.cli.command("init-words")
def init_words_command():
    """Populate the database with the thesis word list."""
    from scripts.parser import update_word_list

    print("Initializing word list (fetching from Cambridge Dictionary)...")
    try:
        count = update_word_list(limit=20)
        print(f"Successfully added {count} words.")
    except Exception as e:
        print(f"Error: {e}")


# --- JIT WARMUP ---
def warmup_audio_engine():
    """
    Executes a dummy analysis on startup to trigger JIT compilation
    for Librosa and Numba functions. This prevents the request from
    being slow for the user.
    """
    # Only run in production (Gunicorn) or when asked, to avoid slowing down dev reload excessively
    # But since user complained, we enable it generally, just logging it.
    try:
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get(
            "GUNICORN_CMD_ARGS"
        ):
            # In Flask Dev server (reloader), this runs twice. WERKZEUG_RUN_MAIN checks if it's the reloader process.
            pass

        app.logger.info("Warming up Audio Engine (JIT Compilation)...")
        import numpy as np
        import soundfile as sf
        import tempfile
        from analysis_engine import analyze_formants_from_path

        # Create 0.5s of silence
        sr = 16000
        y = np.zeros(int(sr * 0.5), dtype=np.float32)

        # Use temp file (Windows fix: close file before soundfile opens it)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()  # Close handle so soundfile can open it on Windows

        try:
            sf.write(tmp_path, y, sr)
            # Run analysis (Trigger JIT)
            # We use a dummy target vowel 'a'
            analyze_formants_from_path(tmp_path, "a")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        app.logger.info("Audio Engine Ready!")
    except Exception as e:
        app.logger.warning(f"Audio Engine Warmup failed: {e}")


# Execute Warmup (Runs on module import)
# We wrap it in a try-block at top level just in case
try:
    warmup_audio_engine()
except:
    pass

if __name__ == "__main__":
    app.run(debug=True)
