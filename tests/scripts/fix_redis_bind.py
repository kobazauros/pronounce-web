from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    print("--- FIXING REDIS BINDING ---")
    # Comment out the default bind line if it exists (usually "bind 127.0.0.1 ::1")
    # And forcefully append/replace with "bind 0.0.0.0" or "bind 127.0.0.1"
    # Safest is to just replace the line if it matches the standard default
    run_remote_command(
        ssh,
        "sed -i 's/^bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf",
        "Update Redis Config",
    )

    # Also explicitly un-comment "bind 127.0.0.1" if it was commented out or set to something else
    # But for now, let's just make sure it's not binding to IPv6 only.
    # Actually, appending might be safer if we are unsure of the file content.
    # Let's try to just append "bind 127.0.0.1" to the end if we are unsure, but redis takes the last one.

    print("\n--- RESTARTING SERVICES ---")
    run_remote_command(ssh, "systemctl restart redis-server", "Restart Redis")
    run_remote_command(ssh, "systemctl restart pronounce-celery", "Restart Celery")

    print("\n--- VERIFYING SOCKETS ---")
    run_remote_command(ssh, "ss -plnt | grep 6379", "Check Port 6379")

    ssh.close()


if __name__ == "__main__":
    main()
