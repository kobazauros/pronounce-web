import os
import re
import requests
import pathlib
import sys
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
SAMPLES_DIR = pathlib.Path(__file__).parent.parent / "samples_new"
PASSWORD = "password123"

TARGET_USERS = ["MichaelDS", "TopQuark", "eggypp"]

# Session cache: username -> requests.Session
user_sessions = {}


def get_session(username, sex="male", country="US"):
    if username in user_sessions:
        return user_sessions[username]

    session = requests.Session()

    # 1. Register
    register_url = f"{BASE_URL}/register"
    # Construct a valid student ID (10 digits) based on hash of username or random
    import random

    student_id = str(random.randint(1000000000, 9999999999))

    payload = {
        "username": username,
        "password": PASSWORD,
        "first_name": username,
        "last_name": "Debug",
        "student_id": student_id,
        "consent": "on",
    }

    try:
        session.post(register_url, data=payload, allow_redirects=True)
    except Exception as e:
        print(f"[-] Registration network error for {username}: {e}")

    # 2. Login
    login_url = f"{BASE_URL}/login"
    login_payload = {"username": username, "password": PASSWORD}

    resp = session.post(login_url, data=login_payload)

    if not any(c.name == "session" for c in session.cookies):
        print(f"[-] Failed to login {username}. Status: {resp.status_code}")
        return None

    user_sessions[username] = session
    return session


def submit_file(word, file_path, username, sex, country):
    session = get_session(username, sex, country)
    if not session:
        return

    upload_url = f"{BASE_URL}/upload"

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "audio/mpeg")}
        data = {"word": word, "testType": "pre"}

        try:
            resp = session.post(upload_url, files=files, data=data)

            print(f"\n--- Submitting {username} / {word} ---")
            if resp.status_code == 200:
                result = resp.json()
                print(json.dumps(result, indent=2))

                analysis = result.get("analysis", {})
                dist_bark = analysis.get("distance_bark")

                if dist_bark is None:
                    print(f"!!! MISSING SCORE for {username} - {word} !!!")
            else:
                print(f"[-] Upload Failed ({resp.status_code}) - {resp.text[:200]}")
        except Exception as e:
            print(f"[!] Error submitting {file_path.name}: {e}")


def main():
    if not SAMPLES_DIR.exists():
        print(f"Error: {SAMPLES_DIR} does not exist.")
        return

    print(f"Scanning {SAMPLES_DIR} for targets: {TARGET_USERS}...")

    files_to_process = []

    for word_dir in SAMPLES_DIR.iterdir():
        if not word_dir.is_dir():
            continue

        word = word_dir.name

        for audio_file in word_dir.glob("*.mp3"):
            match = re.match(r"(.+)_(male|female)_(.+)\.mp3", audio_file.name)
            if match:
                username = match.group(1)
                sex = match.group(2)
                country = match.group(3)

                if username in TARGET_USERS:
                    files_to_process.append(
                        {
                            "word": word,
                            "path": audio_file,
                            "username": username,
                            "sex": sex,
                            "country": country,
                        }
                    )

    print(f"Found {len(files_to_process)} target files. Processing...")

    for item in files_to_process:
        submit_file(
            item["word"], item["path"], item["username"], item["sex"], item["country"]
        )


if __name__ == "__main__":
    main()
