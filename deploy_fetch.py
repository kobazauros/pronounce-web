import os

import requests

# ================= CONFIGURATION =================
# 1. Your PythonAnywhere Username
USERNAME = "kobazauros"

# 2. Your API Token
API_TOKEN = "10226b92b1a2f5dff23f5661ea3043dc5cc949d8"

# 3. Your Domain
DOMAIN_NAME = f"{USERNAME}.pythonanywhere.com"

# 4. Remote Paths (Server)
REMOTE_BASE_PATH = f"/home/{USERNAME}/mysite"
REMOTE_AUDIO_PATH = f"{REMOTE_BASE_PATH}/audio"
REMOTE_SUBMISSIONS_PATH = f"{REMOTE_BASE_PATH}/submissions"
REMOTE_INSTANCE_PATH = f"{REMOTE_BASE_PATH}/instance"
REMOTE_DB_FILE = f"{REMOTE_INSTANCE_PATH}/pronounce.db"

# 5. Local Paths (Computer)
LOCAL_AUDIO_DIR = "/static/audio"
LOCAL_SUBMISSIONS_DIR = "submissions"
LOCAL_INSTANCE_DIR = "instance"
LOCAL_DB_FILE = os.path.join(LOCAL_INSTANCE_DIR, "pronounce.db")

# 6. TASKS TO RUN
DEPLOY_CODE = True
DEPLOY_AUDIO = False
RETRIEVE_SUBMISSIONS = True
SYNC_DB = True
DB_SYNC_DIRECTION = "down"  # 'up' (local->server) or 'down' (server->local)

# 7. Specific Code Files to Sync
FILES_TO_SYNC = [
    "flask_app.py",
    "models.py",
    "config.py",
    "auth_routes.py",
    "dashboard_routes.py",
]

DIRECTORIES_TO_SYNC = ["templates", "static/css", "static/js"]
# =================================================

session = requests.Session()
session.headers.update({"Authorization": f"Token {API_TOKEN}"})


def get_api_url(path):
    return f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{path}"


def upload_file(local_path, remote_path):
    print(f"⬆️  Uploading {os.path.basename(local_path)}...", end=" ")

    if not os.path.exists(local_path):
        print("⚠️ Skipped (Not found)")
        return

    try:
        with open(local_path, "rb") as f:
            response = session.post(get_api_url(remote_path), files={"content": f})
            if response.status_code in [200, 201]:
                print("✅ OK")
            else:
                print(f"❌ Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")


def download_file(remote_path, local_path):
    print(f"⬇️  Downloading {os.path.basename(remote_path)}...", end=" ")

    try:
        response = session.get(get_api_url(remote_path))
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            print("✅ OK")
        else:
            print(f"❌ Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")


def upload_directory(local_dir, remote_dir):
    print(f"📂 Syncing Directory: {local_dir} -> {remote_dir}")
    if not os.path.exists(local_dir):
        print(f"⚠️ Local directory {local_dir} not found.")
        return

    for root, dirs, files in os.walk(local_dir):
        rel_path = os.path.relpath(root, local_dir)
        if rel_path == ".":
            current_remote_dir = remote_dir
        else:
            current_remote_dir = f"{remote_dir}/{rel_path}".replace("\\", "/")

        for file in files:
            local_file_path = os.path.join(root, file)
            remote_file_path = f"{current_remote_dir}/{file}"
            upload_file(local_file_path, remote_file_path)


def list_remote_files(remote_dir):
    """Returns a dict of filenames in a remote directory."""
    response = session.get(get_api_url(remote_dir))
    if response.status_code == 200:
        return response.json()
    return {}


def sync_audio_up():
    print(f"\n--- 🎵 SYNCING AUDIO ({LOCAL_AUDIO_DIR} -> SERVER) ---")

    # 1. Upload index.json first
    json_path = os.path.join(LOCAL_AUDIO_DIR, "index.json")
    if os.path.exists(json_path):
        upload_file(json_path, f"{REMOTE_AUDIO_PATH}/index.json")

    # 2. Upload MP3s
    if not os.path.exists(LOCAL_AUDIO_DIR):
        print(f"⚠️ Local {LOCAL_AUDIO_DIR} folder not found.")
        return

    for filename in os.listdir(LOCAL_AUDIO_DIR):
        if filename.endswith(".mp3"):
            local_p = os.path.join(LOCAL_AUDIO_DIR, filename)
            remote_p = f"{REMOTE_AUDIO_PATH}/{filename}"
            upload_file(local_p, remote_p)


def sync_database(direction="down"):
    """Downloads or uploads the SQLite database file."""
    if direction == "down":
        print("\n--- 💾 SYNCING DATABASE (SERVER -> LOCAL) ---")
        os.makedirs(LOCAL_INSTANCE_DIR, exist_ok=True)
        download_file(REMOTE_DB_FILE, LOCAL_DB_FILE)
    elif direction == "up":
        print("\n--- 💾 SYNCING DATABASE (LOCAL -> SERVER) ---")
        if not os.path.exists(LOCAL_DB_FILE):
            print(f"⚠️ Local database file not found at {LOCAL_DB_FILE}. Skipping.")
            return

        # Safety check to prevent accidental overwrite of production data
        confirm = input(
            "🚨 WARNING: You are about to overwrite the production database. Type 'yes' to confirm: "
        )
        if confirm.lower() == "yes":
            upload_file(LOCAL_DB_FILE, REMOTE_DB_FILE)
        else:
            print("🚫 Upload cancelled.")
    else:
        print(f"⚠️ Invalid DB_SYNC_DIRECTION: '{direction}'. Must be 'up' or 'down'.")


def retrieve_submissions_down():
    print(f"\n--- 📥 RETRIEVING SUBMISSIONS (SERVER -> {LOCAL_SUBMISSIONS_DIR}) ---")

    os.makedirs(LOCAL_SUBMISSIONS_DIR, exist_ok=True)

    # List contents of submissions folder (User IDs)
    root_files = list_remote_files(REMOTE_SUBMISSIONS_PATH)

    for name, details in root_files.items():
        # Assuming directories are user IDs
        if details.get("type") == "directory":
            user_id = name
            remote_user_dir = f"{REMOTE_SUBMISSIONS_PATH}/{user_id}"
            local_user_dir = os.path.join(LOCAL_SUBMISSIONS_DIR, user_id)
            os.makedirs(local_user_dir, exist_ok=True)

            user_files = list_remote_files(remote_user_dir)
            for fname in user_files.keys():
                if fname.endswith(".mp3") or fname.endswith(".wav"):
                    local_p = os.path.join(local_user_dir, fname)
                    if not os.path.exists(local_p):
                        download_file(f"{remote_user_dir}/{fname}", local_p)

    print("✅ Submissions retrieval complete.")


def reload_webapp():
    print("\n--- 🔄 RELOADING SERVER ---")
    url = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN_NAME}/reload/"
    response = session.post(url)
    if response.status_code == 200:
        print("✅ App Reloaded Successfully")
    else:
        print(f"❌ Reload Failed ({response.status_code})")


if __name__ == "__main__":
    print("--- 🚀 STARTING DEPLOYMENT MANAGER ---")

    # 1. Deploy Code
    if DEPLOY_CODE:
        print("\n--- 💻 SYNCING CODE ---")
        for filename in FILES_TO_SYNC:
            upload_file(filename, f"{REMOTE_BASE_PATH}/{filename}")

        for directory in DIRECTORIES_TO_SYNC:
            upload_directory(directory, f"{REMOTE_BASE_PATH}/{directory}")

    # 2. Deploy Audio
    if DEPLOY_AUDIO:
        sync_audio_up()

    # 3. Sync Database
    if SYNC_DB:
        sync_database(DB_SYNC_DIRECTION)

    # 4. Retrieve Submissions
    if RETRIEVE_SUBMISSIONS:
        retrieve_submissions_down()

    # 5. Reload server if we pushed code or the database
    if DEPLOY_CODE or (SYNC_DB and DB_SYNC_DIRECTION == "up"):
        reload_webapp()

    print("\n--- ✨ DONE ---")
