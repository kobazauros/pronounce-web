import os

from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate

from auth_routes import auth
from config import Config
from models import db

# 1. Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# 2. Initialize Extensions
db.init_app(app)
migrate = Migrate(app, db)

# 3. Configure Flask-Login
login_manager = LoginManager(app)
# This ensures that if a user isn't logged in, they are sent to the login page
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login requirement to reload the user object from the session ID."""
    from models import User

    return User.query.get(int(user_id))


# 4. Register Blueprints
# This connects the login/register logic from auth_routes.py to the app
app.register_blueprint(auth)


# 5. Shell Context for Debugging
@app.shell_context_processor
def make_shell_context():
    from models import AnalysisResult, Submission, User, Word

    return {
        "db": db,
        "User": User,
        "Word": Word,
        "Submission": Submission,
        "AnalysisResult": AnalysisResult,
    }


# 6. Main Application Route (Recording Page)
@app.route("/")
@login_required  # Prevents unauthenticated access
def index():
    """
    Renders the main student recording interface.
    Passes the curriculum (20 words) to the frontend.
    """
    from models import Word

    words = Word.query.order_by(Word.sequence_order).all()
    return render_template("index.html", words=words)


# 7. File Upload Route
@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """Handles the audio submission from the frontend."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Create user-specific folder in submissions
    user_folder = os.path.join(app.config["UPLOAD_FOLDER"], str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    # Save the file
    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)

    # Note: In Phase 3, we will add code here to create a Submission
    # record in the DB and trigger the vowel analysis.

    return jsonify({"success": True, "filename": file.filename}), 200


if __name__ == "__main__":
    # Ensure necessary project directories exist for audio and uploads
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)

    # Run the server in debug mode for development
    app.run(debug=True)
