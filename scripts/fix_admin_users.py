from flask import Flask
from sqlalchemy import text
import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, db


def fix_admin_users():
    """
    Ensures all ADMIN users are marked as Secure (is_test_account=False),
    regardless of whether they have an email or not.
    """
    try:
        with app.app_context():
            # SQL command to update admins
            sql = text(
                "UPDATE users SET is_test_account = :false_val WHERE role = 'admin'"
            )

            result = db.session.execute(sql, {"false_val": False})
            db.session.commit()

            print(
                f"Successfully reverted {result.rowcount} ADMIN users to Secure status."
            )

    except Exception as e:
        print(f"Error updating admins: {e}")
        db.session.rollback()


if __name__ == "__main__":
    fix_admin_users()
