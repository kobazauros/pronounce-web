from flask import Flask
from sqlalchemy import text
import os
import sys

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app, db
from models import User


def check_users():
    with app.app_context():
        # Fetch first 10 users
        users = User.query.limit(10).all()
        print(f"{'Username':<20} | {'Email':<30} | {'Is Test?':<10}")
        print("-" * 65)
        for u in users:
            print(f"{u.username:<20} | {str(u.email):<30} | {u.is_test_account}")


if __name__ == "__main__":
    check_users()
