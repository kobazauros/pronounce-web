import argparse
import sys
import os
import json
import paramiko
from pathlib import Path

# COPY FROM deploy.py to ensure standalone execution
PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    if not SFTP_CONFIG_PATH.exists():
        print(f"❌ Error: Config file not found at {SFTP_CONFIG_PATH}")
        sys.exit(1)
    with open(SFTP_CONFIG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding JSON: {e}")
            sys.exit(1)


def get_sftp_client(config):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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


def sync_dir_push(sftp, local_dir, remote_dir):
    """Uploads local directory to remote, recursively."""
    local_path = Path(local_dir)
    print(f"📂 Syncing {local_path} -> {remote_dir}")

    if not local_path.exists():
        print(f"⚠️ Local directory not found: {local_path}")
        return

    # Walk local directory
    for root, dirs, files in os.walk(local_path):
        # Calculate relative path
        rel_path = os.path.relpath(root, local_path)
        # Determine remote directory path
        if rel_path == ".":
            remote_curr_dir = remote_dir
        else:
            # Use forward slashes for remote path (Linux)
            remote_curr_dir = f"{remote_dir}/{rel_path.replace(os.sep, '/')}"

        # Ensure remote directory exists
        try:
            sftp.stat(remote_curr_dir)
        except IOError:
            print(f"   Creating remote dir: {remote_curr_dir}")
            sftp.mkdir(remote_curr_dir)

        for f in files:
            local_file = os.path.join(root, f)
            remote_file = f"{remote_curr_dir}/{f}"

            # Simple check: if size different, upload.
            # (Production robust sync would check mtime, but size/existence is good enough for restoration)
            upload = False
            try:
                r_stat = sftp.stat(remote_file)
                l_stat = os.stat(local_file)
                if r_stat.st_size != l_stat.st_size:
                    upload = True
            except IOError:
                # File doesn't exist remote
                upload = True

            if upload:
                print(f"   ⬆️ Uploading: {f}")
                sftp.put(local_file, remote_file)
            else:
                # print(f"   Skipping {f} (exists)")
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Sync Data between Local and Production"
    )
    parser.add_argument(
        "target", choices=["db", "audio", "submissions", "all"], help="What to sync"
    )
    parser.add_argument(
        "--push", action="store_true", help="Upload LOCAL -> REMOTE (Default is Pull)"
    )
    args = parser.parse_args()

    config = load_config()
    sftp, ssh = get_sftp_client(config)

    remote_root = config.get("remotePath", "/var/www/pronounce-web")

    # Define Paths
    # (Local Path, Remote Path)
    targets = {}

    # Submissions
    targets["submissions"] = (
        os.path.join(PROJECT_ROOT, "submissions"),
        f"{remote_root}/submissions",
    )

    # Audio (Reference)
    targets["audio"] = (
        os.path.join(PROJECT_ROOT, "static", "audio"),
        f"{remote_root}/static/audio",
    )

    # DB
    targets["db"] = (
        os.path.join(PROJECT_ROOT, "instance", "pronounce.db"),
        f"{remote_root}/instance/pronounce.db",
    )

    work_list = []
    if args.target == "all":
        work_list = ["audio", "submissions", "db"]
    else:
        work_list = [args.target]

    for item in work_list:
        local_p, remote_p = targets[item]

        if args.push:
            print(f"🚀 PUSHING {item.upper()}...")
            if item == "db":
                print(
                    "⚠️ DB Push not implemented in this simplified script to prevent overwriting prod DB."
                )
            else:
                sync_dir_push(sftp, local_p, remote_p)
        else:
            print(
                f"📥 PULLING {item.upper()} (Not implemented in this repair script)..."
            )

    sftp.close()
    ssh.close()
    print("✨ Sync Complete.")


if __name__ == "__main__":
    main()
