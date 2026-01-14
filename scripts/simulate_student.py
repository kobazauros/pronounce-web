import os
import requests
import random
import time
import json
import uuid
import statistics
from io import BytesIO

# Configuration
BASE_URL = "https://unaudaciously-vivacious-jaelynn.ngrok-free.dev"
# Unique user every run to ensure clean state
UNIQUE_ID = str(uuid.uuid4())[:8]
USERNAME = f"bench_{UNIQUE_ID}"
PASSWORD = "password123"
# Random 10-digit ID
STUDENT_ID = str(random.randint(1000000000, 9999999999))
FIRST_NAME = "Bench"
LAST_NAME = "Mark"

# Global Metrics
processing_times = []

s = requests.Session()


def register():
    print(f"[*] Registering user '{USERNAME}'...")
    try_url = f"{BASE_URL}/register"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "first_name": FIRST_NAME,
        "last_name": LAST_NAME,
        "student_id": STUDENT_ID,
        "consent": "on",
    }
    # Don't follow redirects to see if we get 302 (success->login) or 200 (form error)
    try:
        resp = s.post(try_url, data=payload, allow_redirects=True)
    except Exception as e:
        print(f"[-] Connection failed to {try_url}: {e}")
        return False

    if resp.status_code == 404:
        try_url = f"{BASE_URL}/auth/register"
        resp = s.post(try_url, data=payload, allow_redirects=True)

    # Success indicators: Redirect to login or "Log In" page
    if resp.url.endswith("/login") or "Log In" in resp.text:
        print("[+] Registration successful (Redirected to login).")
        return True

    if resp.status_code == 200:
        print("[-] Registration returned 200 OK (likely Validation Error).")
        return False  # For benchmark, we want strict success on fresh user

    print(f"[-] Registration failed: {resp.status_code}")
    return False


def login():
    print(f"[*] Logging in as '{USERNAME}'...")
    try_url = f"{BASE_URL}/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    resp = s.post(try_url, data=payload, allow_redirects=True)

    if resp.status_code == 404:
        try_url = f"{BASE_URL}/auth/login"
        resp = s.post(try_url, data=payload, allow_redirects=True)

    if ("Log Out" in resp.text or resp.status_code == 200) and any(
        c.name == "session" for c in s.cookies
    ):
        print(f"[+] Login successful. Session: {s.cookies.get('session')[:8]}...")
        return True

    print(f"[-] Login failed. Status: {resp.status_code}.")
    return False


def get_words():
    # Hardcoded verified list
    return [
        {"word": "bike", "ipa": "baɪk"},
        {"word": "bird", "ipa": "bɜrd"},
        {"word": "moon", "ipa": "mun"},
        {"word": "wait", "ipa": "weɪt"},
        {"word": "cat", "ipa": "kæt"},
        {"word": "boat", "ipa": "boʊt"},
        {"word": "book", "ipa": "bʊk"},
    ]


def perform_test_phase(phase, words):
    print(f"\n=== Starting {phase.upper()} Test Phase ===")

    for item in words:
        word_text = item["word"] if isinstance(item, dict) else item

        # 1. Fetch Sample Audio
        audio_url = f"{BASE_URL}/static/audio/{word_text}.mp3"
        try:
            audio_resp = s.get(audio_url)
            if audio_resp.status_code != 200:
                print(f"    [x] Failed to get sample audio: {word_text}")
                continue
            audio_data = audio_resp.content
        except Exception as e:
            print(f"    [x] Error fetching audio: {e}")
            continue

        # 2. Upload "Imitation"
        files = {"file": (f"{word_text}.mp3", BytesIO(audio_data), "audio/mpeg")}
        data = {"word": word_text, "testType": phase}

        try:
            # --- START TIMER ---
            start_t = time.perf_counter()
            upload_resp = s.post(
                f"{BASE_URL}/upload", files=files, data=data, allow_redirects=False
            )
            end_t = time.perf_counter()
            # --- END TIMER ---

            duration_ms = (end_t - start_t) * 1000

            if upload_resp.status_code in [
                200,
                201,
            ] and "application/json" in upload_resp.headers.get("Content-Type", ""):
                processing_times.append(duration_ms)
                print(f"    [+] '{word_text}' processed in {duration_ms:6.2f} ms")
            else:
                print(
                    f"    [-] Upload failed for '{word_text}': {upload_resp.status_code}"
                )

        except Exception as e:
            print(f"    [x] Upload exception: {e}")

        time.sleep(0.2)


if __name__ == "__main__":
    print(f"=== PRONOUNCE BENCHMARK SCRIPT ===")

    if register():
        if login():
            words = get_words()
            if words:
                perform_test_phase("pre", words)

                print("Computing Stats...")
                if processing_times:
                    stats = {
                        "count": len(processing_times),
                        "avg_ms": round(statistics.mean(processing_times), 2),
                        "median_ms": round(statistics.median(processing_times), 2),
                        "min_ms": round(min(processing_times), 2),
                        "max_ms": round(max(processing_times), 2),
                    }

                    with open("benchmark_stats.json", "w") as f:
                        json.dump(stats, f, indent=4)

                    print(f"Stats saved to benchmark_stats.json")
                else:
                    print(" No successful transactions recorded.")
            else:
                print("[!] No words found.")
    else:
        print("[!] Registration failed.")
