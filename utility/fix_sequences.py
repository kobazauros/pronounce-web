import os
import sys

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from flask_app import app, db
from sqlalchemy import text


def fix_sequences():
    """
    Resets the sequences for all tables to the max(id).
    This fixes the 'duplicate key value violates unique constraint' error
    after a manual data restore.
    """
    tables = [
        "users",
        "words",
        "submissions",
        "analysis_results",
        "invite_codes",
        "password_history",
        "password_reset_tokens",
        # "system_config" has distinct string keys, no sequence usually (check model using db.String PK)
    ]

    with app.app_context():
        print("Fixing sequences...")
        for table in tables:
            try:
                # Construct the SQL to reset the sequence
                # We assume standard naming convention: table_id_seq
                # But safer to use pg_get_serial_sequence if possible.
                sql = text(
                    f"""
                    SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM {table};
                """
                )
                db.session.execute(sql)
                db.session.commit()
                print(f"Fixed sequence for '{table}'.")
            except Exception as e:
                print(f"Skipping '{table}' (might not use sequence or error): {e}")
                db.session.rollback()

        print("Sequence fix complete.")


if __name__ == "__main__":
    fix_sequences()
