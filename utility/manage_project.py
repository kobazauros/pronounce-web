"""
Pronounce Web - Universal Project Manager
Usage:
    python scripts/manage_project.py deploy
    python scripts/manage_project.py pull-db
"""

import sys
import json
import paramiko
import argparse
import subprocess
import os
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    if not SFTP_CONFIG_PATH.exists():
        print(f"❌ Error: Config file not found at {SFTP_CONFIG_PATH}")
        sys.exit(1)
    with open(SFTP_CONFIG_PATH, "r") as f:
        return json.load(f)


def get_ssh_client(config):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Expand user path (e.g. ~/.ssh/id_rsa)
        key_path = os.path.expanduser(config.get("privateKeyPath"))

        print(f"🔌 Connecting to {config['host']} as {config['username']}...")
        ssh.connect(
            hostname=config["host"],
            port=config.get("port", 22),
            username=config["username"],
            key_filename=key_path,
        )
        print("✅ Connected\n")
        return ssh
    except Exception as e:
        print(f"❌ SSH Connection Failed: {e}")
        sys.exit(1)


def run_remote_command(ssh, command, description):
    print(f"🚀 {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        error = stderr.read().decode()
        print(f"❌ Failed: {error}")
        return False
    print(f"✅ Done\n")
    return True


def run_local_command(command, env=None, capture=False):
    result = subprocess.run(
        command, env=env, capture_output=capture, text=True, shell=True
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, result.stdout


# ==========================================
# COMMANDS
# ==========================================


def deploy(config):
    """Deploy latest code to production."""
    print("📢 Starting Deployment...")
    ssh = get_ssh_client(config)
    remote_path = config["remotePath"]

    try:
        # 1. Pull Code
        if not run_remote_command(
            ssh, f"cd {remote_path} && git pull", "Pulling latest code"
        ):
            print("⚠️  Warning: Git pull had issues (conflict?). Proceeding...")

        # DEBUG: Check Python Version
        print("🔍 DEBUG: Checking Remote Python Version...")
        stdin, stdout, stderr = ssh.exec_command("python3 --version")
        print(stdout.read().decode())

        # 2a. Repair Venv (Fix shebangs)
        # Use --clear to force fresh binaries
        run_remote_command(
            ssh,
            f"cd {remote_path} && python3 -m venv .venv --clear",
            "Repairing VirtualEnv (Fresh)",
        )

        # 2. Update Dependencies
        run_remote_command(
            ssh,
            f"cd {remote_path} && source .venv/bin/activate && pip install -r requirements.txt",
            "Updating Dependencies",
        )

        # 3. DB Migration
        run_remote_command(
            ssh,
            f"cd {remote_path} && source .venv/bin/activate && flask db upgrade",
            "Running DB Migrations",
        )

        # 4. Fix Legacy Accounts (New Command)
        # We call the CLI tool we created on the server
        run_remote_command(
            ssh,
            f"cd {remote_path} && source .venv/bin/activate && python utility/manage_admin.py fix-legacy-accounts",
            "Fixing Legacy User Accounts",
        )

        # 5. Restart Services
        run_remote_command(
            ssh, "systemctl restart pronounce-web", "Restarting Web Service"
        )
        run_remote_command(
            ssh, "systemctl restart pronounce-celery", "Restarting Celery Worker"
        )

        print("\n✨ Deployment Complete!")

    finally:
        ssh.close()


def backup_local_db(config, reason="manual"):
    """Backups local database."""
    print(f"📦 Starting Local Backup ({reason})...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{reason}_{timestamp}.sql"
    backup_path = PROJECT_ROOT / "instance" / "backups" / filename

    # Ensure dir exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    LOCAL_DB = "pronounce_db"

    # Assume 'psql' and 'pg_dump' are in same bin dir
    # We re-use logic to find psql to find pg_dump?
    # Or just use PATH if simple? Let's try simple first, fallback to hardcoded.
    pg_dump_cmd = "pg_dump"

    # Try to find pg_dump in likely locations
    possible_paths = [
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            pg_dump_cmd = f'"{p}"'
            break

    env = os.environ.copy()
    env["PGPASSWORD"] = "#Freedom1979"

    cmd = (
        f'{pg_dump_cmd} -U postgres -h localhost -d {LOCAL_DB} -F p -f "{backup_path}"'
    )

    success, out = run_local_command(cmd, env=env)
    if success:
        print(f"✅ Backup created: {backup_path.name}")
        return True
    else:
        print(f"❌ Backup Failed: {out}")
        return False


def pull_db(config, confirm_override=False):
    """Sync Production DB to Local."""
    print("📢 Starting Database Sync (Prod -> Local)...")

    # Confirm
    if not confirm_override:
        confirm = input("⚠️  This will OVERWRITE your local database. Continue? (y/N): ")
        if confirm.lower() != "y":
            print("❌ Cancelled.")
            return

    # AUTO-BACKUP BEFORE DESTRUCTION
    if not backup_local_db(config, reason="pre_sync"):
        print("❌ Pre-sync backup failed. Aborting sync for safety.")
        return

    ssh = get_ssh_client(config)

    # DB Names (Hardcoded or Config?) - Keeping strict as per previous script
    PROD_DB = "pronounce_db"
    PROD_USER = "kobazauros"
    # Using 'postgres' locally to drop/create
    LOCAL_DB = "pronounce_db"

    # Dump Config
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"db_dump_{timestamp}.sql"
    remote_dump_path = f"/tmp/{dump_filename}"
    local_dump_path = PROJECT_ROOT / "instance" / dump_filename

    try:
        # 1. Dump Remote
        # We assume pg_dump matches server credentials logic (or relies on .pgpass/trust)
        # The previous script used PGPASSWORD inline. We should probably do the same if we knew it.
        # But previous script hardcoded password "#Freedom1979". Let's assume it.
        PROD_PW = "#Freedom1979"

        dump_cmd = f'PGPASSWORD="{PROD_PW}" pg_dump -U {PROD_USER} -h localhost -d {PROD_DB} -F p -f {remote_dump_path}'
        if not run_remote_command(ssh, dump_cmd, "Dumping Remote Database"):
            return

        # 2. Download
        print(f"⬇️  Downloading {dump_filename}...")
        sftp = ssh.open_sftp()
        sftp.get(remote_dump_path, str(local_dump_path))
        sftp.close()
        print("✅ Downloaded\n")

        # 3. Cleanup Remote
        ssh.exec_command(f"rm {remote_dump_path}")
        ssh.close()  # Close SSH, we work local now

        # 4. Local Restore
        print("🔄 Restoring Locally...")
        # Use psql from path or explicit?
        # Previous script used: C:\Program Files\PostgreSQL\14\bin\psql.exe
        # We try 'psql' first, else fallback? Or stick to known path.
        # Let's try to assume 'psql' is in PATH or use generic connection via SQLAlchemy? No, psql is better for dumps.

        # We'll use the environment variable PGPASSWORD for local postgres user
        env = os.environ.copy()
        env["PGPASSWORD"] = "#Freedom1979"  # Local postgres/kobazauros password

        # We need to connect to 'postgres' db to drop 'pronounce_db'
        # Assumes 'psql' is in PATH. If previous script worked, maybe it was in PATH?
        # Previous script used: PSQL_PATH = f"{PG_BIN}\\psql.exe"
        # I'll stick to 'psql' command hoping it's in PATH, or try common location?
        # To be safe, let's use the hardcoded path if it exists, else 'psql'.
        possible_paths = [
            r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
            "psql",
        ]
        psql_cmd = "psql"
        for p in possible_paths:
            if p == "psql" or os.path.exists(p):
                psql_cmd = p
                break

        # Terminate connections first
        cmd_terminate = f'"{psql_cmd}" -U postgres -h localhost -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = \'{LOCAL_DB}\' AND pid <> pg_backend_pid();"'
        run_local_command(cmd_terminate, env=env)

        # Drop
        cmd_drop = f'"{psql_cmd}" -U postgres -h localhost -c "DROP DATABASE IF EXISTS {LOCAL_DB}"'
        run_local_command(cmd_drop, env=env)

        # Create
        cmd_create = f'"{psql_cmd}" -U postgres -h localhost -c "CREATE DATABASE {LOCAL_DB} OWNER {PROD_USER}"'
        success, out = run_local_command(cmd_create, env=env)
        if not success:
            print(f"❌ Create DB Failed: {out}")
            return

        # Restore
        # Restore as the OWNER (kobazauros)
        cmd_restore = f'"{psql_cmd}" -U {PROD_USER} -h localhost -d {LOCAL_DB} -f "{local_dump_path}"'
        success, out = run_local_command(cmd_restore, env=env)
        if not success:
            print(f"⚠️  Restore warning (might be non-fatal): {out[:200]}...")

        print(f"\n✅ Sync Complete! Data restored from {dump_filename}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Pronounce Web Project Manager")
    parser.add_argument(
        "command", choices=["deploy", "pull-db", "backup"], help="Command to run"
    )
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--reason", default="manual", help="Reason label for backup")
    args = parser.parse_args()

    config = load_config()

    if args.command == "deploy":
        deploy(config)
    elif args.command == "pull-db":
        pull_db(config, confirm_override=args.yes)
    elif args.command == "backup":
        backup_local_db(config, reason=args.reason)


if __name__ == "__main__":
    main()
