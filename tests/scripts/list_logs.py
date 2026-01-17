from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    run_remote_command(
        ssh, "ls -la /var/www/pronounce-web/logs/", "Listing Logs Directory"
    )

    ssh.close()


if __name__ == "__main__":
    main()
