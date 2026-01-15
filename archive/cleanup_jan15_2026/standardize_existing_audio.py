import os
import sys
from pathlib import Path
import logging

# Add project root to path to import scripts.audio_processing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.audio_processing import process_audio_data

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def standardize_directory(directory: Path):
    """
    Recursively scans a directory for MP3 files and re-processes them.
    """
    logger.info(f"Scanning directory: {directory}")

    count = 0
    errors = 0

    for file_path in directory.rglob("*.mp3"):
        try:
            # Read original
            with open(file_path, "rb") as f:
                raw_bytes = f.read()

            # Process (Resample/Mono/Normalize)
            processed_bytes = process_audio_data(raw_bytes)

            # Write back (Overwrite)
            with open(file_path, "wb") as f:
                f.write(processed_bytes)

            logger.info(f"Processed: {file_path.name}")
            count += 1

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            errors += 1

    logger.info(
        f"Directory {directory.name} complete. Processed: {count}, Errors: {errors}"
    )


def main():
    base_dir = Path(__file__).parent.parent

    # 1. Reference Audio (static/audio)
    ref_dir = base_dir / "static" / "audio"
    if ref_dir.exists():
        standardize_directory(ref_dir)
    else:
        logger.warning(f"Reference directory not found: {ref_dir}")

    # 2. User Submissions (uploads/ folder - configured in config.py but usually 'submissions' or 'static/uploads')
    # Based on config.txt/README, it seems 'submissions' is the legacy folder and 'static/uploads' or 'instance/uploads' might be new?
    # Checking flask_app.py: os.makedirs(app.config["UPLOAD_FOLDER"]...
    # Without loading flask config, let's guess likely locations based on project structure in previous turns.
    # The file structure showed `submissions/`.

    submissions_dir = base_dir / "submissions"
    if submissions_dir.exists():
        standardize_directory(submissions_dir)
    else:
        logger.warning(f"Submissions directory not found: {submissions_dir}")


if __name__ == "__main__":
    main()
