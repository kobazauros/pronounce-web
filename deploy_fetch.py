import requests
import os

# ================= CONFIGURATION =================
# 1. Your PythonAnywhere Username
USERNAME = 'kobazauros'

# 2. Your API Token here.
API_TOKEN = '10226b92b1a2f5dff23f5661ea3043dc5cc949d8'

# 3. Your Domain
DOMAIN_NAME = f'{USERNAME}.pythonanywhere.com'

# 4. Remote Paths (These MATCH your fixed flask_app.py)
REMOTE_BASE_PATH = f'/home/{USERNAME}/mysite'
REMOTE_AUDIO_PATH = f'{REMOTE_BASE_PATH}/audio'
REMOTE_SUBMISSIONS_PATH = f'{REMOTE_BASE_PATH}/submissions'

# 5. Local Paths
LOCAL_AUDIO_DIR = 'audio'
LOCAL_SUBMISSIONS_DIR = 'submissions'

# 6. TASKS TO RUN (Set to True/False)
DEPLOY_CODE = True          # Update script.js, index.html, etc.
DEPLOY_AUDIO = False        # Upload all files from local 'audio/' to server
RETRIEVE_SUBMISSIONS = True # Download student recordings from server

# 7. Specific Code Files to Sync
# Added 'lame.min.js' because your new script.js depends on it!
FILES_TO_SYNC = [
    'script.js',
    'index.html',
    'styles.css',
    'flask_app.py',
    'lame.min.js' 
]
# =================================================

# Create session for connection pooling
session = requests.Session()
session.headers.update({'Authorization': f'Token {API_TOKEN}'})

def get_api_url(path):
    return f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path{path}'

def upload_file(local_path, remote_path):
    """Uploads a single file."""
    print(f"⬆️  Uploading {os.path.basename(local_path)}...", end=" ")
    
    if not os.path.exists(local_path):
        print("⚠️ Skipped (Not found)")
        return

    try:
        with open(local_path, 'rb') as f:
            response = session.post(get_api_url(remote_path), files={'content': f})
            if response.status_code in [200, 201]:
                print("✅ OK")
            else:
                print(f"❌ Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")

def download_file(remote_path, local_path):
    """Downloads a single file."""
    print(f"⬇️  Downloading {os.path.basename(remote_path)}...", end=" ")
    
    try:
        response = session.get(get_api_url(remote_path))
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print("✅ OK")
        else:
            print(f"❌ Failed ({response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")

def list_remote_files(remote_dir):
    """Returns a dict of filenames in a remote directory."""
    response = session.get(get_api_url(remote_dir))
    if response.status_code == 200:
        return response.json() # Returns dict of file info
    return {}

def sync_audio_up():
    """Uploads local audio files to remote audio folder."""
    print(f"\n--- 🎵 SYNCING AUDIO ({LOCAL_AUDIO_DIR} -> SERVER) ---")
    
    # 1. Upload index.json first (Configuration)
    json_path = os.path.join(LOCAL_AUDIO_DIR, 'index.json')
    if os.path.exists(json_path):
        upload_file(json_path, f"{REMOTE_AUDIO_PATH}/index.json")

    # 2. Upload MP3s
    if not os.path.exists(LOCAL_AUDIO_DIR):
        print(f"⚠️ Local {LOCAL_AUDIO_DIR} folder not found.")
        return

    for filename in os.listdir(LOCAL_AUDIO_DIR):
        if filename.endswith('.mp3'):
            local_p = os.path.join(LOCAL_AUDIO_DIR, filename)
            remote_p = f"{REMOTE_AUDIO_PATH}/{filename}"
            upload_file(local_p, remote_p)

def retrieve_submissions_down():
    """Downloads new submissions from server to local."""
    print(f"\n--- 📥 RETRIEVING SUBMISSIONS (SERVER -> {LOCAL_SUBMISSIONS_DIR}) ---")
    
    if not os.path.exists(LOCAL_SUBMISSIONS_DIR):
        os.makedirs(LOCAL_SUBMISSIONS_DIR)

    # 1. Get list of files on server
    files_list = list_remote_files(REMOTE_SUBMISSIONS_PATH)
    
    if not files_list:
        print(f"⚠️ No files found in {REMOTE_SUBMISSIONS_PATH}")
        return

    count = 0
    for filename in files_list.keys():
        if filename.endswith('.mp3'):
            local_p = os.path.join(LOCAL_SUBMISSIONS_DIR, filename)
            
            # Only download if we don't have it yet
            if not os.path.exists(local_p):
                download_file(f"{REMOTE_SUBMISSIONS_PATH}/{filename}", local_p)
                count += 1
    
    if count == 0:
        print("✅ No new submissions to download.")
    else:
        print(f"✅ Downloaded {count} new files.")

def reload_webapp():
    print(f"\n--- 🔄 RELOADING SERVER ---")
    url = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}/webapps/{DOMAIN_NAME}/reload/'
    response = session.post(url)
    if response.status_code == 200:
        print("✅ App Reloaded Successfully")
    else:
        print(f"❌ Reload Failed ({response.status_code})")

if __name__ == "__main__":
    print("--- 🚀 STARTING DEPLOYMENT MANAGER ---")
    
    # 1. Deploy Code
    if DEPLOY_CODE:
        print(f"\n--- 💻 SYNCING CODE ---")
        for filename in FILES_TO_SYNC:
            upload_file(filename, f"{REMOTE_BASE_PATH}/{filename}")

    # 2. Deploy Audio
    if DEPLOY_AUDIO:
        sync_audio_up()

    # 3. Retrieve Submissions
    if RETRIEVE_SUBMISSIONS:
        retrieve_submissions_down()

    # 4. Reload
    if DEPLOY_CODE:
        reload_webapp()
        
    print("\n--- ✨ DONE ---")