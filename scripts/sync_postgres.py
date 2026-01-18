"""
Sync PostgreSQL database from production server to local.

This script:
1. Connects to production server via SSH
2. Dumps the PostgreSQL database using pg_dump
3. Downloads the dump file
4. Restores it to local PostgreSQL database

Usage: python scripts/sync_postgres.py
"""

import sys
import json
import paramiko
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
SFTP_CONFIG_PATH = PROJECT_ROOT / ".vscode" / "sftp.json"


def load_config():
    if not SFTP_CONFIG_PATH.exists():
        print(f"❌ Error: Config file not found at {SFTP_CONFIG_PATH}")
        sys.exit(1)
    with open(SFTP_CONFIG_PATH, "r") as f:
        return json.load(f)


def main():
    print("\n" + "=" * 60)
    print("PostgreSQL Database Sync: Production → Local")
    print("=" * 60 + "\n")

    config = load_config()

    # Production database details (from your server)
    PROD_DB_NAME = "pronounce_db"
    PROD_DB_USER = "kobazauros"
    PROD_DB_PASSWORD = "#Freedom1979"

    # Local database details
    LOCAL_DB_NAME = "pronounce_db"
    LOCAL_DB_USER = "kobazauros"
    LOCAL_DB_PASSWORD = "#Freedom1979"
    LOCAL_DB_HOST = "localhost"
    LOCAL_DB_PORT = "5432"

    # Dump file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"pronounce_db_dump_{timestamp}.sql"
    remote_dump_path = f"/tmp/{dump_filename}"
    local_dump_path = PROJECT_ROOT / "instance" / dump_filename

    print(f"📋 Production DB: {PROD_DB_NAME}")
    print(f"📋 Local DB: {LOCAL_DB_NAME}")
    print(f"📄 Dump file: {dump_filename}\n")

    confirm = input(
        "⚠️  This will REPLACE your local database with production data.\n   Continue? (yes/no): "
    )
    if confirm.lower() not in ["yes", "y"]:
        print("❌ Sync cancelled")
        sys.exit(0)

    try:
        # Connect to production server
        print(f"\n🔌 Connecting to {config['host']}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Properly expand the key path
        import os

        key_path = os.path.expanduser(config.get("privateKeyPath", "~/.ssh/id_rsa"))

        ssh.connect(
            hostname=config["host"],
            port=config.get("port", 22),
            username=config["username"],
            key_filename=key_path,
        )
        print("✅ Connected to production server\n")

        # Step 1: Dump production database
        print("📦 Dumping production database...")
        dump_cmd = f'PGPASSWORD="{PROD_DB_PASSWORD}" pg_dump -U {PROD_DB_USER} -h localhost -d {PROD_DB_NAME} -F p -f {remote_dump_path}'
        stdin, stdout, stderr = ssh.exec_command(dump_cmd)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error = stderr.read().decode()
            print(f"❌ Dump failed: {error}")
            ssh.close()
            sys.exit(1)

        print("✅ Database dumped successfully\n")

        # Step 2: Download dump file
        print(f"⬇️  Downloading dump file...")
        sftp = ssh.open_sftp()
        sftp.get(remote_dump_path, str(local_dump_path))
        sftp.close()
        print(f"✅ Downloaded to {local_dump_path}\n")

        # Step 3: Clean up remote dump file
        print("🧹 Cleaning up remote dump file...")
        ssh.exec_command(f"rm {remote_dump_path}")
        ssh.close()
        print("✅ Remote cleanup complete\n")

        # PostgreSQL binary path
        PG_BIN = r"C:\Program Files\PostgreSQL\14\bin"
        PSQL_PATH = f"{PG_BIN}\\psql.exe"

        # Step 4: Drop and recreate local database
        print("🗑️  Dropping local database...")
        drop_cmd = [
            PSQL_PATH,
            "-U",
            "postgres",
            "-h",
            LOCAL_DB_HOST,
            "-p",
            LOCAL_DB_PORT,
            "-c",
            f"DROP DATABASE IF EXISTS {LOCAL_DB_NAME}",
        ]

        # Set PGPASSWORD environment variable for postgres user
        import os

        env = os.environ.copy()
        env["PGPASSWORD"] = "#Freedom1979"  # Your postgres password

        result = subprocess.run(drop_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Drop database warning: {result.stderr}")

        print("📝 Creating fresh local database...")
        create_cmd = [
            PSQL_PATH,
            "-U",
            "postgres",
            "-h",
            LOCAL_DB_HOST,
            "-p",
            LOCAL_DB_PORT,
            "-c",
            f"CREATE DATABASE {LOCAL_DB_NAME} OWNER {LOCAL_DB_USER}",
        ]

        result = subprocess.run(create_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Create database failed: {result.stderr}")
            sys.exit(1)

        print("✅ Local database recreated\n")

        # Step 5: Restore dump to local database
        print("📥 Restoring database from dump...")
        env["PGPASSWORD"] = LOCAL_DB_PASSWORD
        restore_cmd = [
            PSQL_PATH,
            "-U",
            LOCAL_DB_USER,
            "-h",
            LOCAL_DB_HOST,
            "-p",
            LOCAL_DB_PORT,
            "-d",
            LOCAL_DB_NAME,
            "-f",
            str(local_dump_path),
        ]

        result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Restore warnings: {result.stderr[:500]}")

        print("✅ Database restored successfully\n")

        # Step 6: Verify data
        print("🔍 Verifying data...")
        verify_cmd = [
            PSQL_PATH,
            "-U",
            LOCAL_DB_USER,
            "-h",
            LOCAL_DB_HOST,
            "-p",
            LOCAL_DB_PORT,
            "-d",
            LOCAL_DB_NAME,
            "-c",
            "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM words; SELECT COUNT(*) FROM submissions;",
        ]

        result = subprocess.run(verify_cmd, env=env, capture_output=True, text=True)
        print(result.stdout)

        print("\n" + "=" * 60)
        print("✅ Sync Complete!")
        print("=" * 60)
        print(f"\n📄 Dump file saved at: {local_dump_path}")
        print("💡 You can delete it after verifying the sync\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
