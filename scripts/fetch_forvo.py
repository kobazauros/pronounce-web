# pyright: strict
import os
import requests
import base64
import re
import time
import random

import collections
from typing import Dict, List, Optional, Tuple, cast
from bs4 import BeautifulSoup

# Configuration
COOKIE_FILE = "forvo_cookies.txt"
DATASET_DIR = "dataset/forvo"
BASE_URL = "https://forvo.com"
AUDIO_HOSTS = [
    "https://audio00.forvo.com/audios/mp3",
    "https://audio10.forvo.com/audios/mp3",
    "https://audio.forvo.com/audios/mp3",
]

WORDS = [
    "bike",
    "bird",
    "boat",
    "book",
    "boy",
    "cake",
    "call",
    "cat",
    "chair",
    "cow",
    "cup",
    "dark",
    "ear",
    "green",
    "hot",
    "moon",
    "red",
    "sit",
    "tour",
    "wait",
]

# Database to store scan results
# Format: { word: [ {user: "username", url: "decoded_path", id: "123", country: "en"} ] }
scan_db: Dict[str, List[Dict[str, str]]] = collections.defaultdict(list)


def decode_forvo_path(b64_str: str) -> Optional[str]:
    try:
        if not b64_str:
            return None
        return base64.b64decode(b64_str).decode("utf-8")
    except Exception:
        return None


def get_cookies() -> Tuple[Dict[str, str], str]:
    print("\n[!] Forvo Login Required")
    print("1. Open https://forvo.com in your browser.")
    print("2. Log in.")
    print("3. Open Developer Tools (F12) -> Network Tab.")
    print("4. Copy the 'Cookie' header string.")
    print("5. Copy the 'User-Agent' header string.")

    cookie_str = input("Paste Cookie String: ").strip()
    ua_str = input("Paste User-Agent String: ").strip()

    with open(COOKIE_FILE, "w") as f:
        f.write(cookie_str + "\n" + ua_str)

    return parse_cookies(cookie_str), ua_str


def load_auth() -> Tuple[Dict[str, str], str]:
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                print("[+] Loaded auth from file.")
                return parse_cookies(lines[0].strip()), lines[1].strip()

    return get_cookies()


def parse_cookies(cookie_str: str) -> Dict[str, str]:
    cookies = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cast(Dict[str, str], cookies)


def scan_page(session: requests.Session, word: str) -> None:
    url = f"{BASE_URL}/word/{word}/"
    print(f"[*] Scanning metadata: {word}...")

    try:
        resp = session.get(url)
    except Exception as e:
        print(f"[-] Request failed: {e}")
        return

    if resp.status_code != 200:
        print(f"[-] Status {resp.status_code}")
        return

    soup = BeautifulSoup(resp.content, "html.parser")

    # Logic: Find 'en' container or just iterate list items that have 'Play'
    # Use generic approach: find all li with class 'pronunciation'
    items = soup.find_all("li", class_="pronunciation")

    found_count = 0
    for li in items:
        # Extract User
        user_span = li.find("span", class_="ofLink")
        username = user_span.get("data-p2") if user_span else "unknown"

        # Extract Audio ID and Path from onclick="Play(...)"
        # onclick="Play(189754,'ODk...','ODk...', ...)"
        play_div = li.find("div", onclick=re.compile(r"Play\("))
        if not play_div:
            continue

        onclick_val = str(play_div["onclick"])
        # Regex to capture content inside Play(...)
        # We expect: Play(id, b64_mp3, b64_ogg, ...)
        match = re.search(r"Play\((\d+),'([^']+)','([^']+)'", onclick_val)
        if match:
            _id, b64_mp3, _ = match.groups()
            path_mp3 = decode_forvo_path(cast(str, b64_mp3))
            country = (
                "Unknown"  # Default since scraping country is complex from this view
            )

            if path_mp3:
                # Store candidate
                entry = {
                    "user": username,
                    "id": _id,
                    "path": path_mp3,
                    "word": word,
                    "country": country,
                }
                scan_db[word].append(cast(Dict[str, str], entry))
                found_count += 1

    print(f"    -> Found {found_count} recordings.")


def analyze_and_select() -> List[Dict[str, str]]:
    print("\n=== ANALYZING TOP SPEAKERS ===")

    # 1. Count user frequency across ALL words
    user_counts: collections.Counter[str] = collections.Counter()
    for word, recordings in scan_db.items():
        unique_users_for_word = set(r["user"] for r in recordings)
        for u in unique_users_for_word:
            user_counts[u] += 1

    # 2. Print Top Power Users
    print("Top Speakers in this set:")
    top_speakers: List[Tuple[str, int]] = user_counts.most_common(10)
    for u, count in top_speakers:
        print(f"  - {u}: {count} words")

    # 3. Selection Strategy
    # We want at least 3 recordings per word.
    # We prefer users with HIGHER total word counts (minimize distinct IDs).

    selected_download_list: List[Dict[str, str]] = []

    for word in WORDS:
        candidates: List[Dict[str, str]] = scan_db.get(word, [])
        if not candidates:
            print(f"Warning: No recordings for '{word}'")
            continue

        # Sort candidates:
        # Priority 1: User total coverage (descending)
        # Priority 2: Random/ID (stable tie break)

        candidates.sort(key=lambda x: user_counts[x["user"]], reverse=True)

        # Pick top 3 (or fewer if not enough)
        best_pics = candidates[:3]
        selected_download_list.extend(best_pics)

        users_picked = [p["user"] for p in best_pics]
        print(f"Selected for '{word}': {users_picked}")

    return selected_download_list


def download_files(
    session: requests.Session, selection_list: List[Dict[str, str]]
) -> None:
    print(f"\n=== DOWNLOADING {len(selection_list)} FILES ===")

    success_count = 0
    for item in selection_list:
        username = item["user"]
        word = item["word"]
        r_path = item["path"]

        # Organize by User (Persona)
        # dataset/forvo/{username}/{word}.mp3
        user_dir = os.path.join(DATASET_DIR, username)
        os.makedirs(user_dir, exist_ok=True)

        save_path = os.path.join(user_dir, f"{word}.mp3")

        if os.path.exists(save_path):
            print(f"[Skipping] {username}/{word}.mp3 (Exists)")
            continue

        # Download attempt
        downloaded = False
        for host in AUDIO_HOSTS:
            url = f"{host}/{r_path}"
            try:
                # Polite delay before download
                time.sleep(random.uniform(0.5, 1.5))

                resp = session.get(
                    url, headers={"Referer": "https://forvo.com/"}, stream=True
                )
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"[+] Downloaded: {username}/{word}.mp3")
                    downloaded = True
                    break
            except Exception:
                continue

        if downloaded:
            success_count += 1
        else:
            print(f"[-] Failed: {username}/{word}")

    print(f"\nDone. {success_count}/{len(selection_list)} files downloaded.")


def main():
    print("=== FORVO CRAWLER v2.1 (Anti-403) ===")

    cookies, user_agent = load_auth()

    headers = {
        "User-Agent": user_agent,
        "Referer": "https://forvo.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
    }

    s = requests.Session()
    s.cookies.update(cookies)  # type: ignore
    s.headers.update(headers)

    # Phase 1: Scan
    for word in WORDS:
        scan_page(s, word)
        time.sleep(random.uniform(2, 4))  # Polite scan delay

    # Phase 2: Select
    downloads = analyze_and_select()

    # Phase 3: Download
    if downloads:
        cmd = input(f"\nProceed to download {len(downloads)} files? (y/n): ")
        if cmd.lower() == "y":
            download_files(s, downloads)
    else:
        print("Nothing to download.")


if __name__ == "__main__":
    main()
