from flask_app import app, db, User
import sys
import os

# Ensure we can import from current directory
sys.path.append(os.getcwd())

with app.app_context():
    try:
        count = User.query.count()
        print(f"Total Users: {count}")

        users = User.query.filter(User.username.notlike("loadtest_%")).all()
        print(f"Real Users found: {len(users)}")
        for u in users:
            print(f"- {u.username} (ID: {u.student_id})")
    except Exception as e:
        print(f"Error querying DB: {e}")
