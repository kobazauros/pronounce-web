from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize extensions (to be imported in app.py)
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Handles Students, Teachers, and Admins.
    Roles: 'student' (default), 'teacher', 'admin'
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Login Credentials
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Personal Info
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)

    # Role-Specific Data
    # Nullable because Teachers/Admins don't have student IDs
    student_id = db.Column(db.String(20), unique=True, nullable=True, index=True)

    # Role Enforcement: 'student', 'teacher', 'admin'
    role = db.Column(db.String(20), default="student", nullable=False)

    # Privacy & Legal
    # CRITICAL: If None, user cannot record/upload. Must be set to datetime.now(timezone.utc) upon agreement.
    consented_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    submissions = db.relationship("Submission", backref="user", lazy="dynamic")

    def __init__(
        self,
        username=None,
        first_name=None,
        last_name=None,
        student_id=None,
        role="student",
        consented_at=None,
    ):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.student_id = student_id
        self.role = role
        self.consented_at = consented_at

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Word(db.Model):
    """
    The Source of Truth for the Curriculum.
    Contains exactly 20 rows (the thesis word list).
    """

    __tablename__ = "words"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64), unique=True, nullable=False)  # e.g., 'moon'
    sequence_order = db.Column(db.Integer, nullable=False)  # 1 to 20

    # Phonetic Data
    ipa = db.Column(db.String(64), nullable=True)  # e.g., /muːn/
    vowels = db.Column(db.String(64), nullable=True)  # e.g., uː
    stressed_vowel = db.Column(db.String(10), nullable=True)  # e.g., uː

    # Reference Audio
    audio_path = db.Column(db.String(256), nullable=True)  # Path to MP3

    # Relationships
    submissions = db.relationship("Submission", backref="target_word", lazy="dynamic")

    def __repr__(self):
        return f"<Word {self.sequence_order}: {self.text}>"


class Submission(db.Model):
    """
    Represents one audio recording uploaded by a user.
    """

    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Context
    # Foreign Key ensures strict adherence to the 20-word list
    word_id = db.Column(db.Integer, db.ForeignKey("words.id"), nullable=False)
    test_type = db.Column(db.String(10), default="pre")  # 'pre' or 'post'

    # File Storage
    # Naming Convention: submissions/{user_id}/{uuid}.mp3
    file_path = db.Column(db.String(256), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # One-to-One Relationship to analysis
    analysis = db.relationship(
        "AnalysisResult",
        backref="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __init__(
        self,
        user_id=None,
        word_id=None,
        test_type="pre",
        file_path=None,
        file_size_bytes=None,
    ):
        self.user_id = user_id
        self.word_id = word_id
        self.test_type = test_type
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes

    def __repr__(self):
        return f"<Submission {self.id}: User {self.user_id}>"


class AnalysisResult(db.Model):
    """
    Stores the acoustic analysis data.
    """

    __tablename__ = "analysis_results"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )

    # 1. Raw Formants (Measured from Student)
    f1_raw = db.Column(db.Float)
    f2_raw = db.Column(db.Float)

    # 2. Reference Formants (Target Model)
    f1_ref = db.Column(db.Float)
    f2_ref = db.Column(db.Float)

    # 3. VTLN Data (Normalization)
    scaling_factor = db.Column(db.Float, default=1.0)  # The 'alpha'
    f1_norm = db.Column(db.Float)  # Student F1 / alpha
    f2_norm = db.Column(db.Float)  # Student F2 / alpha

    # 4. Scores
    distance_hz = db.Column(db.Float)  # Euclidean distance in Hz
    distance_bark = db.Column(db.Float)  # Perceptual distance

    # 5. Diagnostic Flags
    is_deep_voice_corrected = db.Column(
        db.Boolean, default=False
    )  # True if 4000Hz ceiling was used
    is_outlier = db.Column(db.Boolean, default=False)  # True if score > threshold

    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Analysis Result for Sub #{self.submission_id}>"


class SystemConfig(db.Model):
    """Stores key-value system configuration settings."""

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value

    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value}>"

    @staticmethod
    def get(key, default=None):
        """Helper to get a config value by key."""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def get_bool(key, default=False):
        """Helper to get a config value as a boolean."""
        val = SystemConfig.get(key)
        if val is None:
            return default
        return val.lower() in ["true", "1", "t", "y", "yes"]

    @staticmethod
    def set(key, value):
        """Helper to set a config value. The value is converted to a string."""
        config = SystemConfig.query.filter_by(key=key).first()
        if not config:
            config = SystemConfig(key=key, value=str(value))
            db.session.add(config)  # type: ignore
        else:
            config.value = str(value)
        # No commit here, let the caller handle the transaction
