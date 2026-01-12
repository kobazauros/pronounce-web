"""
Bidirectional file synchronization script for PythonAnywhere.

Usage:
    python sync_project_files.py up   - Deploys the entire local project to the server.
    python sync_project_files.py down - Fetches the entire server project to local.

WARNING:
    - 'up' will overwrite server files with your local versions.
    - 'down' will overwrite your local files with server versions.
    Use with caution.
"""

import os
import sys
from time import sleep

import requests

# ================= CONFIGURATION =================
# 1. Your PythonAnywhere Username
USERNAME = "kobazauros"

# 2. Your API Token (Find it in your PythonAnywhere Account -> API Token)
API_TOKEN = "10226b92b1a2f5dff23f5661ea3043dc5cc949d8"

# 3. Your Domain
DOMAIN_NAME = f"{USERNAME}.pythonanywhere.com"

# 4. Remote Base Path (The root directory of your project on the server)
REMOTE_BASE_PATH = f"/home/{USERNAME}/mysite"

# 5. Local Base Path (The root directory of your project on this computer)
# 5. Local Base Path (The root directory of your project on this computer)
# Gets the parent of the 'utility' directory
LOCAL_BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 6. Directories and files to IGNORE during synchronization
#    Uses .gitignore-style patterns.
IGNORE_PATTERNS = [
    ".git/",
    ".venv/",
    "__pycache__/",
    ".vscode/",
    "*.pyc",
    "*.log",
    "*.log.*",
    ".DS_Store",
    "*.ipynb",
    "*.csv",
    "road_map.md",
]
# =================================================

session = requests.Session()
session.headers.update({"Authorization": f"Token {API_TOKEN}"})


def get_api_url(path):
    """Constructs the full PythonAnywhere API URL for a given path."""
    return f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{path}"


def upload_file(local_path, remote_path):
    """Uploads a single file to the remote server."""
    print(
        f"⬆️  Uploading {os.path.relpath(local_path, LOCAL_BASE_PATH)}...",
        end=" ",
        flush=True,
    )

    if not os.path.exists(local_path):
        print("⚠️ Skipped (Not found)")
        return

    try:
        with open(local_path, "rb") as f:
            response = session.post(get_api_url(remote_path), files={"content": f})
            if response.status_code in [200, 201]:
                print("✅ OK")
            else:
                print(f"❌ Failed ({response.status_code}: {response.text})")
            sleep(1.5)  # To avoid hitting rate limits
    except Exception as e:
        print(f"❌ Error: {e}")


def download_file(remote_path, local_path):
    """Downloads a single file from the remote server."""
    print(
        f"⬇️  Downloading {os.path.relpath(remote_path, REMOTE_BASE_PATH)}...",
        end=" ",
        flush=True,
    )

    try:
        response = session.get(get_api_url(remote_path))
        if response.status_code == 200:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)
            print("✅ OK")
        else:
            print(f"❌ Failed ({response.status_code}: {response.text})")
    except Exception as e:
        print(f"❌ Error: {e}")


def list_remote_files_recursive(remote_dir):
    """Recursively lists all files and directories from a remote path."""
    file_list = []

    # Use a stack to manage directories to visit, starting with the root
    stack = [remote_dir]

    while stack:
        current_dir = stack.pop()

        # Ensure the API path doesn't have a trailing slash for listing
        api_list_url = get_api_url(current_dir.rstrip("/"))

        try:
            response = session.get(api_list_url)
            if response.status_code != 200:
                print(
                    f"❌ Failed to list remote directory {current_dir}: {response.text}"
                )
                continue

            contents = response.json()
            if isinstance(contents, dict):  # It's a directory listing
                for name, details in contents.items():
                    full_path = f"{current_dir}/{name}"
                    if details.get("type") == "directory":
                        stack.append(full_path)
                    else:  # It's a file
                        file_list.append(full_path)
            elif isinstance(
                contents, list
            ):  # It's a file content response (should not happen here)
                # This can happen if the 'remote_dir' was actually a file
                file_list.append(current_dir)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing remote directory {current_dir}: {e}")

    return file_list


def get_local_files_recursive():
    """
    Walks the local project directory and returns a list of file paths
    to sync, respecting IGNORE_PATTERNS.
    """
    import fnmatch
    from pathlib import Path

    files_to_sync = []
    local_path = Path(LOCAL_BASE_PATH)

    # Use posix-style paths for patterns.
    dir_patterns = [p for p in IGNORE_PATTERNS if p.endswith("/")]
    file_patterns = [p for p in IGNORE_PATTERNS if not p.endswith("/")]

    for p in local_path.rglob("*"):
        if not p.is_file():
            continue

        try:
            rel_path = p.relative_to(local_path)
        except ValueError:
            # This can happen if the file is outside the local base path, though
            # rglob shouldn't allow it. Better to be safe.
            continue

        rel_path_posix = rel_path.as_posix()

        is_ignored = False

        # 1. Check file patterns (e.g. '*.pyc', 'LICENSE')
        for pattern in file_patterns:
            if fnmatch.fnmatch(rel_path.name, pattern) or fnmatch.fnmatch(
                rel_path_posix, pattern
            ):
                is_ignored = True
                break
        if is_ignored:
            continue

        # 2. Check directory patterns (e.g. '.git/', 'node_modules/')
        # This checks if the path starts with an ignored directory pattern.
        for pattern in dir_patterns:
            if rel_path_posix.startswith(pattern):
                is_ignored = True
                break
        if is_ignored:
            continue

        # 3. Check if any parent directory component is ignored (e.g., '**/__pycache__/').
        path_parts_with_slashes = {f"{part}/" for part in rel_path.parent.parts}
        for pattern in dir_patterns:
            if pattern in path_parts_with_slashes:
                is_ignored = True
                break
        if is_ignored:
            continue

        files_to_sync.append(str(p))

    return files_to_sync


def reload_webapp():
    """Reloads the PythonAnywhere web app to apply changes."""
    print("\n--- 🔄 RELOADING SERVER ---")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN_NAME}/reload/"
    response = session.post(url)
    if response.status_code == 200:
        print("✅ App Reloaded Successfully")
    else:
        print(f"❌ Reload Failed ({response.status_code}: {response.text})")


def sync_up():
    """Synchronizes local files to the server."""
    print("--- 🚀 STARTING SYNC UP (LOCAL -> SERVER) ---")

    # Safety check
    confirm = input(
        "🚨 WARNING: This will overwrite server files with your local versions. Type 'yes' to confirm: "
    )
    if confirm.lower() != "yes":
        print("🚫 Sync cancelled.")
        return

    local_files = get_local_files_recursive()
    print(f"Found {len(local_files)} files to upload.")

    for local_path in local_files:
        rel_path = os.path.relpath(local_path, LOCAL_BASE_PATH).replace("\\", "/")
        remote_path = f"{REMOTE_BASE_PATH}/{rel_path}"
        upload_file(local_path, remote_path)

    reload_webapp()
    print("\n--- ✨ SYNC UP COMPLETE ---")


def sync_down():
    """Synchronizes remote files to the local machine."""
    print("--- 🚀 STARTING SYNC DOWN (SERVER -> LOCAL) ---")

    # Safety check
    confirm = input(
        "🚨 WARNING: This will overwrite local files with server versions. Type 'yes' to confirm: "
    )
    if confirm.lower() != "yes":
        print("🚫 Sync cancelled.")
        return

    remote_files = list_remote_files_recursive(REMOTE_BASE_PATH)
    print(f"Found {len(remote_files)} files to download.")

    for remote_path in remote_files:
        rel_path = os.path.relpath(remote_path, REMOTE_BASE_PATH).replace("\\", "/")
        local_path = os.path.join(LOCAL_BASE_PATH, rel_path)
        download_file(remote_path, local_path)

    print("\n--- ✨ SYNC DOWN COMPLETE ---")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["up", "down"]:
        print(__doc__)
        sys.exit(1)

    direction = sys.argv[1]

    if direction == "up":
        sync_up()
    elif direction == "down":
        sync_down()
