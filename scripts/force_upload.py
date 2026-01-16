from scripts.deploy import load_config, get_sftp_client


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    local_base = "c:/Users/rookie/Documents/Projects/pronounce-web"
    remote_base = "/var/www/pronounce-web"

    files = ["flask_app.py", "tasks.py", "analysis_engine.py"]

    print("--- FORCE UPLOADING FILES ---")
    for f in files:
        print(f"Uploading {f}...")
        sftp.put(f"{local_base}/{f}", f"{remote_base}/{f}")

    print("\n--- RESTARTING SERVICES ---")
    ssh.exec_command("systemctl restart pronounce-web pronounce-celery")

    sftp.close()
    ssh.close()
    print("Done.")


if __name__ == "__main__":
    main()
