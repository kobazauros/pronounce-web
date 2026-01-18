"""
Migrate existing users to 'test account' status.

Rules:
1. All existing users are marked as Test Accounts.
2. EXCEPT users with 'admin' role.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask_app import create_app
from models import db, User


def run_migration():
    app = create_app()
    with app.app_context():
        print("Migrating users to Test Account status...")

        # Update all non-admins to be test accounts
        updated_count = User.query.filter(User.role != "admin").update(
            {User.is_test_account: True}, synchronize_session=False
        )

        db.session.commit()

        print(f"✅ Successfully marked {updated_count} users as Test Accounts.")
        print(f"ℹ️ Admins were excluded.")

        # Verify
        admin_count = User.query.filter_by(role="admin").count()
        test_count = User.query.filter_by(is_test_account=True).count()

        print(f"\nStats:")
        print(f"  Test Users: {test_count}")
        print(f"  Admins: {admin_count}")


if __name__ == "__main__":
    run_migration()
