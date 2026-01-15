import subprocess
import sys


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["models.py"]
    print(f"Running mypy on {targets}...")
    try:
        cmd = ["mypy"] + targets
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr
        with open("mypy_output.txt", "w", encoding="utf-8") as f:
            f.write(output)
        print("Done. Output written to mypy_output.txt")
    except Exception as e:
        print(f"Error: {e}")
