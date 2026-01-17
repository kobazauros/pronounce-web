# pyright: strict

import re
import requests
import pathlib
from typing import Any, Dict, List, Optional

# Configuration
BASE_URL = "http://127.0.0.1:5000"
SAMPLES_DIR = pathlib.Path(__file__).parent.parent / "samples_new"
PASSWORD = "password123"

# Session cache: username -> requests.Session
user_sessions: Dict[str, requests.Session] = {}


def get_session(
    username: str, sex: str = "male", country: str = "US"
) -> Optional[requests.Session]:
    """
    Returns a logged-in session for the given username.
    Registers the user if not already tracked in this run (or if registration fails appropriately).
    """
    if username in user_sessions:
        return user_sessions[username]

    session = requests.Session()

    # 1. Register
    # Based on flask_app.py, auth blueprint is at root, so /register
    register_url = f"{BASE_URL}/register"
    # Construct a valid student ID (10 digits) based on hash of username or random
    # Using a fixed mapping or random for simplicity, ensuring uniqueness is handled by server or assume fresh db
    # For simplicity, let's generate a pseudo-random 10 digit ID
    import random

    student_id = str(random.randint(1000000000, 9999999999))

    payload = {
        "username": username,
        "password": PASSWORD,
        "first_name": username,
        "last_name": "Sample",
        "student_id": student_id,
        "consent": "on",
    }

    try:
        resp = session.post(register_url, data=payload, allow_redirects=True)
        # 200 OK likely means rendered template (error or success msg), 302 means redirect (success)
    except Exception as e:
        print(f"[-] Registration network error for {username}: {e}")

    # 2. Login
    login_url = f"{BASE_URL}/login"
    login_payload = {"username": username, "password": PASSWORD}

    resp = session.post(login_url, data=login_payload)

    if resp.status_code == 200 and "Log Out" in resp.text:
        # Verify login success by checking text or current_user logic if possible
        # The simplest check is if we are NOT on the login page anymore
        pass

    # Basic check: did we get a session cookie?
    if not any(c.name == "session" for c in session.cookies):
        print(f"[-] Failed to login {username}. Status: {resp.status_code}")
        # print(resp.text[:200]) # Debug
        return None

    user_sessions[username] = session
    return session


def submit_file(
    word: str, file_path: pathlib.Path, username: str, sex: str, country: str
) -> None:
    session = get_session(username, sex, country)
    if not session:
        return

    upload_url = f"{BASE_URL}/upload"

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "audio/mpeg")}
        data = {"word": word, "testType": "pre"}  # Defaulting to 'pre' test

        try:
            resp = session.post(upload_url, files=files, data=data)

            if resp.status_code == 200:
                result = resp.json()
                analysis = result.get("analysis", {})
                dist_bark = analysis.get("distance_bark")
                vowel = analysis.get("vowel")
                print(
                    f"[+] {username} ({sex}, {country}) -> {word}: Success. Dist: {dist_bark} Bark ({vowel})"
                )
            else:
                print(
                    f"[-] {username} -> {word}: Upload Failed ({resp.status_code}) - {resp.text[:100]}"
                )
        except Exception as e:
            print(f"[!] Error submitting {file_path.name}: {e}")


def main():
    if not SAMPLES_DIR.exists():
        print(f"Error: {SAMPLES_DIR} does not exist.")
        return

    print(f"Scanning {SAMPLES_DIR}...")

    # Structure: samples_new/word/username_sex_country.mp3

    files_to_process: List[Dict[str, Any]] = []

    for word_dir in SAMPLES_DIR.iterdir():
        if not word_dir.is_dir():
            continue

        word = word_dir.name

        for audio_file in word_dir.glob("*.mp3"):
            # Parse filename
            # Expected: username_sex_country.mp3
            # Note: username might contain underscores, so we might need robust parsing if structurize_samples did that.
            # structurize_samples: "{nickname}_{sex}_{country}.mp3"
            # It used match.group(1), (2), (3).
            # If nickname has underscores, the regex `(.+)_(male|female)_(.+)` is greedy on group 1.

            match = re.match(r"(.+)_(male|female)_(.+)\.mp3", audio_file.name)
            if match:
                username = match.group(1)
                sex = match.group(2)
                country = match.group(3)

                files_to_process.append(
                    {
                        "word": word,
                        "path": audio_file,
                        "username": username,
                        "sex": sex,
                        "country": country,
                    }
                )
            else:
                print(f"Skipping format mismatch: {audio_file.name}")

    print(f"Found {len(files_to_process)} files. Processing...")

    for item in files_to_process:
        submit_file(
            item["word"], item["path"], item["username"], item["sex"], item["country"]
        )


if __name__ == "__main__":
    main()
