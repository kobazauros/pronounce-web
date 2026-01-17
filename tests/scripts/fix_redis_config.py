from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    # helper to add env var if not exists
    def add_env(service, key, value):
        # destructive sed: append after [Service]
        # We assume [Service] exists.
        cmd = f'grep -q "{key}" /etc/systemd/system/{service} || sed -i \'/[Service]/a Environment="{key}={value}"\' /etc/systemd/system/{service}'
        run_remote_command(ssh, cmd, f"Adding {key} to {service}")

    print("Fixing Redis Config on Server...")

    # Web Service
    add_env("pronounce-web.service", "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    add_env(
        "pronounce-web.service", "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"
    )

    # Celery Service
    add_env("pronounce-celery.service", "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    add_env(
        "pronounce-celery.service", "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"
    )

    print("Reloading Systemd...")
    run_remote_command(ssh, "systemctl daemon-reload", "Daemon Reload")

    print("Restarting Services...")
    run_remote_command(
        ssh, "systemctl restart pronounce-web pronounce-celery", "Restart Services"
    )

    ssh.close()


if __name__ == "__main__":
    main()
