import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    print(f"--- {description} ---")
    print(f"Running: {command}")
    try:
        subprocess.check_call(command, shell=True)
        print("✅ Success\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}\n")
        # Don't exit, try to continue


def setup_pythonanywhere():
    print("🚀 Starting Setup for PythonAnywhere...\n")

    # 1. Install Requirements
    print("📦 Step 1: Installing Dependencies...")
    run_command("pip install -r requirements.txt", "Pip Install")

    # 2. Database Migrations
    print("🗄️ Step 2: Database Initialization...")
    if not os.path.exists("instance"):
        os.makedirs("instance")

    # Run Flask DB commands
    # Ensure FLASK_APP works
    os.environ["FLASK_APP"] = "flask_app.py"

    run_command("flask db upgrade", "Database Upgrade")

    # 3. Static Files Check
    print("static Step 3: Static Files Warning")
    print("Make sure you have set up the Static Files mapping in the Web Tab!")
    print("URL: /static/")
    print(f"Directory: {os.getcwd()}/static/")
    print("\n")

    print("🎉 Setup Complete! Reload your Web App in the PythonAnywhere Console.")


if __name__ == "__main__":
    setup_pythonanywhere()
