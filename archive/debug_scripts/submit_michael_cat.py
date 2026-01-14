import requests
import pathlib
import json

BASE_URL = "http://127.0.0.1:5000"
FILE_PATH = "samples_new/cat/MichaelDS_male_UK.mp3"
USERNAME = "MichaelDS"
PASSWORD = "password123"


def run():
    session = requests.Session()
    session.post(f"{BASE_URL}/login", data={"username": USERNAME, "password": PASSWORD})

    path = pathlib.Path(__file__).parent.parent / FILE_PATH
    if not path.exists():
        print(f"File missing: {path}")
        return

    with open(path, "rb") as f:
        files = {"file": (path.name, f, "audio/mpeg")}
        data = {"word": "cat", "testType": "pre"}
        resp = session.post(f"{BASE_URL}/upload", files=files, data=data)

        print(f"Status: {resp.status_code}")
        try:
            res = resp.json()
            print(json.dumps(res, indent=2))
            print(f"Distance: {res.get('analysis', {}).get('distance_bark')}")
        except:
            print(resp.text)


if __name__ == "__main__":
    run()
