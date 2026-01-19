# pyright: strict
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Basic Security
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key-please-change-in-production"

    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. SQLite fallback is disabled."
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Development Settings
    TEMPLATES_AUTO_RELOAD = True

    # Mail Settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_SENDER") or "noreply@pronounce-web.com"
    )

    # File Storage
    UPLOAD_FOLDER = os.path.join(basedir, "submissions")
    AUDIO_FOLDER = os.path.join(basedir, "static", "audio")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # Celery / Redis
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
