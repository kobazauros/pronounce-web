import os
import sys
import logging
from typing import Type

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_app import app, db
from models import User, Word, Submission, AnalysisResult, InviteCode, SystemConfig

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_data():
    """
    Migrates data from the current Flask-SQLAlchemy DB (SQLite) to a target PostgreSQL DB.
    """
    postgres_uri = os.environ.get("DATABASE_URL")

    # Interactive Prompt if missing
    if not postgres_uri:
        print("DATABASE_URL not found in environment.")
        print("Please enter PostgreSQL credentials to connect and migrate:")

        db_user = input("DB User (default: postgres): ").strip() or "postgres"
        db_pass = input("DB Password (leave blank if none): ").strip()
        db_host = input("DB Host (default: localhost): ").strip() or "localhost"
        db_name = input("DB Name (default: pronounce_db): ").strip() or "pronounce_db"

        if db_pass:
            postgres_uri = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        else:
            postgres_uri = f"postgresql://{db_user}@{db_host}/{db_name}"

        print(f"\nConstructed URI: {postgres_uri}")

        # Persistence Prompt
        save = input("Save this to .env file for future use? (y/N): ").strip().lower()
        if save == "y":
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
            )
            try:
                with open(env_path, "a") as f:
                    f.write(f"\nDATABASE_URL={postgres_uri}\n")
                print(f"Saved to {env_path}")
            except Exception as e:
                logger.error(f"Failed to write .env: {e}")

    if not postgres_uri:
        logger.error("No DATABASE_URL provided. Exiting.")
        sys.exit(1)

    logger.info("Starting migration...")
    logger.info(
        f"Target Database: {postgres_uri.split('@')[-1]}"
    )  # Log safe part of URI

    # 1. Load Data from Source (SQLite)
    # We use the Flask App Context to query the current DB
    with app.app_context():
        logger.info("Reading data from Source (SQLite)...")
        users = User.query.all()
        words = Word.query.order_by(Word.sequence_order).all()  # type: ignore
        submissions = Submission.query.all()
        results = AnalysisResult.query.all()
        invites = InviteCode.query.all()
        configs = SystemConfig.query.all()

        logger.info(f"Found {len(users)} Users")
        logger.info(f"Found {len(words)} Words")
        logger.info(f"Found {len(submissions)} Submissions")
        logger.info(f"Found {len(results)} AnalysisResults")
        logger.info(f"Found {len(invites)} InviteCodes")
        logger.info(f"Found {len(configs)} SystemConfigs")

    # 2. Connect to Target (PostgreSQL)
    # create a clean SQLAlchemy engine (bypass Flask-SQLAlchemy)
    pg_engine = create_engine(postgres_uri)
    SessionVals = sessionmaker(bind=pg_engine)
    pg_session = SessionVals()

    try:
        # 3. Create Tables in Target
        # access the underlying MetaData from our Flask models
        logger.info("Creating tables in Target DB...")
        db.metadata.create_all(pg_engine)

        # 4. Insert Data (In Order)

        # --- USERS ---
        logger.info("Migrating Users...")
        for u in users:
            # Detach object from source session by expunging or creating copy
            # Simplest is to create new instance or merge, but we want to keep IDs
            # Assuming target DB is empty, we can just merge/add.
            # However, because they are attached to the 'app.db' session, we must be careful.
            # We will create new dictionary representations to insert.

            # Helper to clone
            pg_session.merge(u)
            # Note: merge() copies the state of the object into the session.
            # It works well across sessions/engines.
        pg_session.commit()

        # --- WORDS ---
        logger.info("Migrating Words...")
        for w in words:
            pg_session.merge(w)
        pg_session.commit()

        # --- SUBMISSIONS ---
        logger.info("Migrating Submissions...")
        for s in submissions:
            pg_session.merge(s)
        pg_session.commit()

        # --- ANALYSIS RESULTS ---
        logger.info("Migrating AnalysisResults...")
        for r in results:
            pg_session.merge(r)
        pg_session.commit()

        # --- INVITE CODES ---
        logger.info("Migrating InviteCodes...")
        for i in invites:
            pg_session.merge(i)
        pg_session.commit()

        # --- SYSTEM CONFIG ---
        logger.info("Migrating SystemConfigs...")
        for c in configs:
            pg_session.merge(c)
        pg_session.commit()

        logger.info("Migration Completed Successfully!")

    except Exception as e:
        logger.error(f"Migration Failed: {e}")
        pg_session.rollback()
        sys.exit(1)
    finally:
        pg_session.close()


if __name__ == "__main__":
    migrate_data()
