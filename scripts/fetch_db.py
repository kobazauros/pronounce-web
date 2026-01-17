import sys
import os
from pathlib import Path
import json
import paramiko

# Reuse logic from sync_data.py
PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    with open(SFTP_CONFIG_PATH, "r") as f:
        return json.load(f)


def download_db():
    config = load_config()
    key_path = os.path.expanduser(config.get("privateKeyPath"))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config["host"], username=config["username"], key_filename=key_path
    )
    sftp = ssh.open_sftp()

    remote_db = "/var/www/pronounce-web/instance/pronounce.db"
    local_db = os.path.join(PROJECT_ROOT, "instance", "temp_prod.db")

    print(f"⬇️ Downloading DB: {remote_db} -> {local_db}")
    sftp.get(remote_db, local_db)

    sftp.close()
    ssh.close()
    print("✅ Done.")


if __name__ == "__main__":
    download_db()
