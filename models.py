from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize extensions (to be imported in app.py)
db: SQLAlchemy = SQLAlchemy()


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
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        student_id: str | None = None,
        role: str = "student",
        consented_at: datetime | None = None,
    ):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.student_id = student_id
        self.role = role
        self.consented_at = consented_at

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
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

    def __init__(
        self,
        text: str | None = None,
        sequence_order: int | None = None,
        ipa: str | None = None,
        vowels: str | None = None,
        stressed_vowel: str | None = None,
        audio_path: str | None = None,
    ):
        self.text = text
        self.sequence_order = sequence_order
        self.ipa = ipa
        self.vowels = vowels
        self.stressed_vowel = stressed_vowel
        self.audio_path = audio_path

    def __repr__(self) -> str:
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
        user_id: int | None = None,
        word_id: int | None = None,
        test_type: str = "pre",
        file_path: str | None = None,
        file_size_bytes: int | None = None,
    ):
        self.user_id = user_id
        self.word_id = word_id
        self.test_type = test_type
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes

    def __repr__(self) -> str:
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

    def __init__(self, submission_id: int | None = None) -> None:
        self.submission_id = submission_id

    def __repr__(self) -> str:
        return f"<Analysis Result for Sub #{self.submission_id}>"


class SystemConfig(db.Model):
    """Stores key-value system configuration settings."""

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __init__(self, key: str | None = None, value: str | None = None):
        self.key = key
        self.value = value

    def __repr__(self) -> str:
        return f"<SystemConfig {self.key}={self.value}>"

    @staticmethod
    def get(key: str, default: str | None = None) -> str | None:
        """Helper to get a config value by key."""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Helper to get a config value as a boolean."""
        val = SystemConfig.get(key)
        if val is None:
            return default
        return val.lower() in ["true", "1", "t", "y", "yes"]

    @staticmethod
    def set(key: str, value: str | int | bool) -> None:
        """Helper to set a config value. The value is converted to a string."""
        config = SystemConfig.query.filter_by(key=key).first()
        # No commit here, let the caller handle the transaction
        if not config:
            config = SystemConfig(key=key, value=str(value))
            db.session.add(config)
        else:
            config.value = str(value)


class InviteCode(db.Model):
    """
    Stores invite codes for teacher registration.
    """

    __tablename__ = "invite_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Tracking usage
    is_used = db.Column(db.Boolean, default=False)
    used_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    creator = db.relationship(
        "User", foreign_keys=[created_by], backref="created_invites"
    )
    used_by = db.relationship(
        "User", foreign_keys=[used_by_user_id], backref="used_invite"
    )

    def __init__(self, code: str, created_by: int):
        self.code = code
        self.created_by = created_by

    def __repr__(self):
        return f"<InviteCode {self.code} (Used: {self.is_used})>"
