from flask import Flask
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, db


def update_legacy_users():
    """
    Updates all users with no email (or empty email) to be marked as 'Legacy' (is_test_account=True).
    """
    try:
        with app.app_context():
            # SQL command to update users
            sql = text(
                "UPDATE users SET is_test_account = :true_val WHERE email IS NULL OR email = ''"
            )

            result = db.session.execute(sql, {"true_val": True})
            db.session.commit()

            print(f"Successfully updated {result.rowcount} users to Legacy status.")

    except Exception as e:
        print(f"Error updating users: {e}")
        db.session.rollback()


if __name__ == "__main__":
    update_legacy_users()
