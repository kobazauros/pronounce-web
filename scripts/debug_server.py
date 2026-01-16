from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    print("Checking App Logs...")
    run_remote_command(
        ssh, "tail -n 50 /var/www/pronounce-web/logs/pronounce.log", "Fetching App Logs"
    )

    ssh.close()


if __name__ == "__main__":
    main()
