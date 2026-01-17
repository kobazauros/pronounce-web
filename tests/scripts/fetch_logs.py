from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    print("\n--- TASKS.PY HEAD ---")
    run_remote_command(ssh, "head -n 15 /var/www/pronounce-web/tasks.py", "Head Tasks")

    print("\n--- FLASK_APP.PY SNIPPET ---")
    run_remote_command(
        ssh, "sed -n '60,80p' /var/www/pronounce-web/flask_app.py", "Slice Flask"
    )

    ssh.close()


if __name__ == "__main__":
    main()
