import argparse
import sys
import time
import json
import os
import paramiko
from pathlib import Path

# Constants for Config Loading
PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    """Load SFTP configuration from .vscode/sftp.json"""
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


def run_remote_command(ssh, command, description):
    """Execute a command on the remote server and print output."""
    print(f"🚀 {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)

    # Stream output
    exit_status = stdout.channel.recv_exit_status()

    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if out:
        print(f"  [stdout] {out}")
    if err:
        print(f"  [stderr] {err}")

    if exit_status != 0:
        print(f"❌ Command failed with exit code {exit_status}")
        return False

    print("✅ Done.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Deploy updates to production server via SSH"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reset (git reset --hard) before pulling",
    )
    args = parser.parse_args()

    config = load_config()
    # We only need the SSH client, not SFTP
    sftp, ssh = get_sftp_client(config)
    sftp.close()  # Close SFTP channel, keep SSH open

    remote_path = config["remotePath"]

    commands = [
        # 1. Navigate to project
        (f"cd {remote_path}", "Navigating to project directory"),
        # 2. Update Code
        (f"cd {remote_path} && git fetch --all", "Fetching latest code"),
    ]

    if args.force:
        commands.append(
            (
                f"cd {remote_path} && git reset --hard origin/main",
                "HARD RESET to match GitHub",
            )
        )
    else:
        commands.append((f"cd {remote_path} && git pull", "Pulling latest changes"))

    # 3. Update Dependencies
    commands.extend(
        [
            (
                f"cd {remote_path} && source .venv/bin/activate && pip install -r requirements.txt",
                "Installing/Updating dependencies",
            ),
            # 4. Restart Services
            (f"sudo systemctl restart pronounce-web", "Restarting Web Server"),
            (
                f"sudo systemctl restart pronounce-celery",
                "Restarting Background Worker",
            ),
        ]
    )

    print("📢 Starting Automated Deployment...")
    print("-----------------------------------")

    total_start = time.time()
    for cmd, desc in commands:
        if not run_remote_command(ssh, cmd, desc):
            print("\n🛑 Deployment Aborted due to error.")
            ssh.close()
            sys.exit(1)

    ssh.close()
    duration = time.time() - total_start
    print("-----------------------------------")
    print(f"✨ Deployment Completed Successfully in {duration:.1f}s!")


if __name__ == "__main__":
    main()
