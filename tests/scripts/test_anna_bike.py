import requests
import json
import time
import os

BASE_URL = "https://209.17.118.73"
USER_EMAIL = "anna@example.com"  # Making up an email for 'anna'
USER_PASS = "123456"
USER_NAME = "anna"
AUDIO_FILE = r"c:\Users\rookie\Documents\Projects\pronounce-web\static\audio\bike.mp3"

session = requests.Session()
session.verify = False  # Self-signed cert or IP direct access


def register_or_login():
    # Try Login
    print(f"Logging in as {USER_NAME}...")
    res = session.post(
        f"{BASE_URL}/auth/login", data={"email": USER_EMAIL, "password": USER_PASS}
    )

    # Check if we are really logged in (look for logout link or session cookie usage)
    print(f"Login Response URL: {res.url}")
    if "/dashboard" in res.url or "logout" in res.text.lower():
        print("Login successful.")
        return

    print("Login might have failed, trying to register...")
    # Try Register
    res = session.post(
        f"{BASE_URL}/auth/register",
        data={
            "first_name": USER_NAME,
            "last_name": "Test",
            "email": USER_EMAIL,
            "password": USER_PASS,
            "confirm_password": USER_PASS,
        },
    )
    print(f"Register status: {res.status_code}")

    # Login again
    res = session.post(
        f"{BASE_URL}/auth/login", data={"email": USER_EMAIL, "password": USER_PASS}
    )
    if "logout" not in res.text.lower():
        print(
            "WARNING: Login still seems to have failed. Response might be login page."
        )


def find_word_id(target_word):
    print("Fetching word list...")
    res = session.get(f"{BASE_URL}/api/word_list")
    if res.status_code != 200:
        print(f"Failed to get word list: {res.status_code}")
        print(f"Response URL: {res.url}")
        return None

    try:
        words = res.json()
    except Exception as e:
        print(f"JSON Error: {e}")
        print(f"Response Text head: {res.text[:200]}")
        return None
    for w in words:
        if w["word"].lower() == target_word.lower():
            return w["id"]
    return None


def main():
    register_or_login()

    word_id = find_word_id("bike")
    if not word_id:
        print("Error: Word 'bike' not found in database.")
        return

    print(f"Found word 'bike' with ID: {word_id}")

    # Step 1: Process Audio
    print("Uploading audio for processing...")
    with open(AUDIO_FILE, "rb") as f:
        files = {"audio": ("bike.mp3", f, "audio/mpeg")}
        res = session.post(f"{BASE_URL}/api/process_audio", files=files)

    if res.status_code != 200:
        print(f"Process failed: {res.text}")
        return

    data = res.json()
    temp_path = data.get("temp_path")
    if not temp_path:
        print("No temp_path in response")
        return
    print(f"Audio processed. Temp path: {temp_path}")

    # Step 2: Submit Recording
    print("Submitting recording...")
    payload = {"word_id": word_id, "file_path": temp_path, "test_type": "post"}
    res = session.post(f"{BASE_URL}/api/submit_recording", json=payload)

    if res.status_code != 202:
        print(f"Submission failed: {res.text}")
        return

    submit_data = res.json()
    task_id = submit_data.get("task_id")
    print(f"Submission accepted. Task ID: {task_id}")

    # Step 3: Poll Status
    print("Polling for results...")
    for i in range(20):  # 20 seconds timeout
        time.sleep(1)
        res = session.get(f"{BASE_URL}/api/status/{task_id}")
        data = res.json()
        status = data.get("status")
        print(f"Poll {i+1}: {status}")

        if status == "success":
            print("\nSUCCESS! Analysis Complete.")
            print(json.dumps(data, indent=2))
            return
        elif status == "error":
            print("\nFAILURE! Analysis Error.")
            print(json.dumps(data, indent=2))
            return

    print("\nTimeout waiting for analysis.")


if __name__ == "__main__":
    main()
