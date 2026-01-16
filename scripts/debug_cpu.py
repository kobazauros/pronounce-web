from scripts.deploy import load_config, get_sftp_client, run_remote_command


def main():
    config = load_config()
    sftp, ssh = get_sftp_client(config)

    script = """
import psutil
import time
print(f"Interval 0.1s: {psutil.cpu_percent(interval=0.1)}%")
print(f"Interval 0.5s: {psutil.cpu_percent(interval=0.5)}%")
print(f"Interval 1.0s: {psutil.cpu_percent(interval=1.0)}%")

# Check Load Avg
if hasattr(psutil, "getloadavg"):
    print(f"Load Avg: {psutil.getloadavg()}")
"""

    # Write temp script on server
    run_remote_command(
        ssh, "cat > /tmp/cpu_test.py <<EOF" + script + "\nEOF", "Creating Test Script"
    )

    # Run it
    run_remote_command(
        ssh, "/var/www/pronounce-web/.venv/bin/python /tmp/cpu_test.py", "Running Test"
    )

    ssh.close()


if __name__ == "__main__":
    main()
