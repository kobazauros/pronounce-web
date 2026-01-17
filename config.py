# pyright: strict
import os


class Config:
    # Basic Security
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-please-change-in-production"

    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "instance", "pronounce.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Development Settings
    TEMPLATES_AUTO_RELOAD = True

    # File Storage
    UPLOAD_FOLDER = os.path.join(basedir, "submissions")
    AUDIO_FOLDER = os.path.join(basedir, "static", "audio")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # Celery / Redis
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
