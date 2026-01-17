import os
import re
import requests
import concurrent.futures
import time
import random
import uuid
from pathlib import Path

# Configuration
BASE_URL = "https://209.17.118.73"  # Production IP (HTTPS)
DATASET_DIR = os.path.join("dataset", "forvo")
MAX_WORKERS = 50  # Adjust based on expected concurrency

# Regex to parse filenames: nickname_sex_country.mp3
# Example: Atalina_female_US.mp3
FILENAME_PATTERN = re.compile(
    r"(?P<nickname>.+)_(?P<sex>male|female)_(?P<country>UK|US)\.mp3"
)


def get_users_and_files(dataset_path):
    """
    Scans the dataset directory and groups files by user (nickname).
    Returns a dict: { nickname: [ { 'path': ..., 'word': ... }, ... ] }
    """
    users = {}
    dataset = Path(dataset_path)

    if not dataset.exists():
        print(f"Error: Dataset directory {dataset_path} not found.")
        return {}

    # Walk through word folders (e.g., dataset/forvo/bike/...)
    for word_dir in dataset.iterdir():
        if not word_dir.is_dir():
            continue

        word = word_dir.name
        for audio_file in word_dir.glob("*.mp3"):
            match = FILENAME_PATTERN.match(audio_file.name)
            if match:
                nickname = match.group("nickname")
                if nickname not in users:
                    users[nickname] = []

                users[nickname].append(
                    {"path": str(audio_file), "word": word, "filename": audio_file.name}
                )

    return users


class StudentSimulator:
    def __init__(self, nickname, files):
        self.nickname = nickname
        self.files = files
        self.session = requests.Session()
        self.session.verify = False  # Ignore SSL warnings for IP

        # Suppress warnings
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # User details (as requested)
        self.username = f"{nickname}_test3"
        self.password = "password123"
        self.first_name = f"{nickname}_test3"
        self.last_name = f"{nickname}_test3"
        # ID starting with 000, 10 digits total (so 7 random digits)
        self.student_id = f"000{random.randint(1000000, 9999999)}"

        self.results = []

    def log(self, msg):
        print(f"[{self.nickname}] {msg}")

    def get_csrf_token(self, url):
        try:
            resp = self.session.get(url)
            # Simple regex to find the token
            match = re.search(r'name="csrf_token" value="([^"]+)"', resp.text)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def register(self):
        url = f"{BASE_URL}/register"
        csrf = self.get_csrf_token(url)

        payload = {
            "csrf_token": csrf,
            "username": self.username,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "student_id": self.student_id,
            "consent": "on",
            "email": f"{self.username}@example.com",
            "confirm_password": self.password,
        }

        try:
            resp = self.session.post(url, data=payload, allow_redirects=True)
            if resp.status_code == 200 or resp.url.endswith("/login"):
                return True
            self.log(f"Register failed: {resp.status_code}")
        except Exception as e:
            self.log(f"Register error: {e}")
        return False

    def login(self):
        url = f"{BASE_URL}/login"
        csrf = self.get_csrf_token(url)

        payload = {
            "csrf_token": csrf,
            "username": self.username,  # Form likely expects 'username' based on auth_routes.py
            "password": self.password,
        }

        # Retry loop
        for attempt in range(2):
            try:
                resp = self.session.post(url, data=payload)

                if "/login" not in resp.url and (
                    resp.status_code == 200 or resp.status_code == 302
                ):
                    return True

                if "Invalid" in resp.text:
                    self.log(f"Login failed: Invalid credentials.")
                    return False

                time.sleep(1)
            except Exception as e:
                self.log(f"Login error: {e}")

        self.log(f"Login failed after retries. Final URL: {resp.url}")
        return False

    def get_word_map(self):
        """Fetches word list to map text to IDs."""
        try:
            resp = self.session.get(f"{BASE_URL}/api/word_list")
            if resp.status_code == 200:
                try:
                    words = resp.json()
                    return {w["word"].lower(): w["id"] for w in words}
                except ValueError:
                    self.log(
                        f"Word list returned HTML (likely redirect). First 50 chars: {resp.text[:50]}"
                    )
            else:
                self.log(f"Failed to get word list: {resp.status_code}")
        except Exception as e:
            self.log(f"Word list error: {e}")
        return {}

    def submit_and_poll(self, file_info, word_map):
        upload_url = f"{BASE_URL}/api/process_audio"
        submit_url = f"{BASE_URL}/api/submit_recording"

        word_text = file_info["word"].lower()
        word_id = word_map.get(word_text)

        if not word_id:
            self.log(f"Skipping '{word_text}': ID not found in word list.")
            return False

        try:
            # 1. Upload Audio
            with open(file_info["path"], "rb") as f:
                # API expects 'audio' field
                files = {"audio": (file_info["filename"], f, "audio/mpeg")}

                start_time = time.time()
                # POST /api/process_audio
                up_resp = self.session.post(upload_url, files=files)

                if up_resp.status_code != 200:
                    self.log(
                        f"Audio upload failed for {word_text}: {up_resp.status_code}"
                    )
                    return False

                up_data = up_resp.json()
                file_path = up_data.get("path")
                if not file_path:
                    self.log(f"No path returned for {word_text}")
                    return False

                # 2. Submit Recording
                submission_payload = {
                    "word_id": word_id,
                    "file_path": file_path,
                    "test_type": "pre",
                }

                sub_resp = self.session.post(submit_url, json=submission_payload)

                if sub_resp.status_code != 202:
                    self.log(
                        f"Submission failed for {word_text}: {sub_resp.status_code}"
                    )
                    return False

                task_id = sub_resp.json().get("task_id")

                # 3. Poll Status
                status_url = f"{BASE_URL}/api/status/{task_id}"
                while True:
                    poll_resp = self.session.get(status_url)
                    status_data = poll_resp.json()

                    if status_data.get("status") == "success":
                        duration = time.time() - start_time
                        self.log(f"Success: {word_text} ({duration:.2f}s)")
                        self.results.append(duration)
                        return True
                    elif status_data.get("status") == "error":
                        self.log(
                            f"Analysis Error for {word_text}: {status_data.get('message')}"
                        )
                        return False

                    time.sleep(1)
                    if (time.time() - start_time) > 60:
                        self.log(f"Timeout processing {word_text}")
                        return False

        except Exception as e:
            self.log(f"Error processing {word_text}: {e}")
            return False

    def run(self):
        self.log("Starting...")
        if self.register():
            # Small delay to mimic human/network variance
            time.sleep(random.uniform(0.1, 0.5))
            if self.login():
                self.log("Logged in.")

                # Fetch word map once logged in
                word_map = self.get_word_map()
                if not word_map:
                    self.log("Could not fetch word map. Aborting.")
                    return False

                for file_info in self.files:
                    self.submit_and_poll(file_info, word_map)
                self.log(f"Finished {len(self.files)} files.")
                return True
        return False


import argparse


def main():
    parser = argparse.ArgumentParser(description="Concurrency Stress Test")
    parser.add_argument(
        "--users", type=int, default=0, help="Max users to simulate (0 = all)"
    )
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between starts")
    args = parser.parse_args()

    print("--- 🚀 Concurrency Stress Test ---")
    print(f"Target: {BASE_URL}")
    print(f"Scanning {DATASET_DIR}...")

    users_dict = get_users_and_files(DATASET_DIR)
    print(f"Found {len(users_dict)} unique users in dataset.")

    # Select subset if requested
    all_nicknames = list(users_dict.keys())
    if args.users > 0 and args.users < len(all_nicknames):
        selected_nicknames = all_nicknames[: args.users]
        print(f"Limiting to first {args.users} users.")
    else:
        selected_nicknames = all_nicknames

    simulators = []
    for nickname in selected_nicknames:
        simulators.append(StudentSimulator(nickname, users_dict[nickname]))

    print(f"Starting simulation with {len(simulators)} workers...")
    start_all = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for sim in simulators:
            futures.append(executor.submit(sim.run))
            if args.delay > 0:
                time.sleep(args.delay)
        concurrent.futures.wait(futures)

    total_duration = time.time() - start_all
    print(f"\n--- ✅ Test Complete in {total_duration:.2f}s ---")


if __name__ == "__main__":
    main()
