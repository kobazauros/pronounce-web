import json
import os
import argparse
import paramiko
from pathlib import Path
import sys

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    """Load SFTP configuration from .vscode/sftp.json"""
    if not SFTP_CONFIG_PATH.exists():
        print(f"❌ Error: Config file not found at {SFTP_CONFIG_PATH}")
        sys.exit(1)

    with open(SFTP_CONFIG_PATH, "r") as f:
        try:
            # Handle potential comments in JSONC if necessary (simple load for now)
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding JSON: {e}")
            sys.exit(1)


def get_sftp_client(config):
    """Establish SFTP connection using config"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Handle key path expansion
        key_path = os.path.expanduser(config.get("privateKeyPath"))

        print(f"🔌 Connecting to {config['host']} as {config['username']}...")
        ssh.connect(
            hostname=config["host"],
            port=config.get("port", 22),
            username=config["username"],
            key_filename=key_path,
        )

        return ssh.open_sftp(), ssh
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)


def sync_directory(sftp, local_dir, remote_dir, direction="pull"):
    """Sync a directory recursively.
    direction: 'pull' (Remote -> Local) or 'push' (Local -> Remote)
    """
    if direction == "pull":
        print(f"📥 Pulling from {remote_dir} -> {local_dir}")
        os.makedirs(local_dir, exist_ok=True)

        try:
            # List remote files
            for entry in sftp.listdir_attr(str(remote_dir)):
                remote_path = str(Path(remote_dir) / entry.filename)
                local_path = local_dir / entry.filename

                if entry.st_mode & 0o040000:  # Is directory
                    sync_directory(sftp, local_path, remote_path, direction)
                else:
                    # File sync logic (simple overwite for now, can add timestamp check)
                    print(f"  - Downloading {entry.filename}")
                    sftp.get(remote_path, str(local_path))

        except FileNotFoundError:
            print(f"⚠️ Remote directory {remote_dir} does not exist.")

    elif direction == "push":
        print(f"📤 Pushing from {local_dir} -> {remote_dir}")
        # Ensure remote dir exists (basic check)
        try:
            sftp.stat(str(remote_dir))
        except FileNotFoundError:
            print(f"  - Creating remote dir {remote_dir}")
            sftp.mkdir(str(remote_dir))

        for item in os.listdir(local_dir):
            local_path = local_dir / item
            remote_path = str(Path(remote_dir) / item)

            if local_path.is_dir():
                sync_directory(sftp, local_path, remote_path, direction)
            else:
                print(f"  - Uploading {item}")
                sftp.put(str(local_path), remote_path)


def main():
    parser = argparse.ArgumentParser(
        description="Sync data files (DB, Audio, Submissions) via SFTP"
    )
    parser.add_argument(
        "target", choices=["db", "audio", "submissions", "all"], help="What to sync"
    )
    parser.add_argument(
        "--push", action="store_true", help="Upload Local -> Remote (DANGEROUS for DB)"
    )
    args = parser.parse_args()

    config = load_config()
    sftp, ssh = get_sftp_client(config)

    remote_root = Path(config["remotePath"])
    local_root = Path(config.get("localPath", str(PROJECT_ROOT)))

    try:
        # DB Sync
        if args.target in ["db", "all"]:
            remote_db = remote_root / "instance" / "pronounce.db"
            local_db = local_root / "instance" / "pronounce.db"

            if args.push:
                confirm = input(
                    "⚠️ CRITICAL: You are about to OVERWRITE the PRODUCTION database with your local copy. Are you sure? (yes/no): "
                )
                if confirm.lower() == "yes":
                    print(f"📤 Uploading DB to {remote_db}")
                    sftp.put(str(local_db), str(remote_db))
                else:
                    print("🛑 Upload cancelled.")
            else:
                print(f"📥 Downloading DB from {remote_db}")
                os.makedirs(local_db.parent, exist_ok=True)
                try:
                    sftp.get(str(remote_db), str(local_db))
                    print("✅ Database downloaded successfully.")
                except FileNotFoundError:
                    print("❌ Remote database not found.")

        # Submissions Sync (Recursive)
        if args.target in ["submissions", "all"]:
            remote_sub = remote_root / "submissions"
            local_sub = local_root / "submissions"
            direction = "push" if args.push else "pull"
            sync_directory(sftp, local_sub, str(remote_sub), direction)

        # Audio Sync (Recursive)
        if args.target in ["audio", "all"]:
            remote_audio = remote_root / "static" / "audio"
            local_audio = local_root / "static" / "audio"
            direction = "push" if args.push else "pull"
            sync_directory(sftp, local_audio, str(remote_audio), direction)

    finally:
        sftp.close()
        ssh.close()
        print("🔌 Connection closed.")


if __name__ == "__main__":
    main()
