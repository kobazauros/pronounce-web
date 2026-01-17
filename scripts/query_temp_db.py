# pyright: strict
import sqlite3
import sys


def query_submission(filename: str) -> None:
    db_path = "instance/temp_prod.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Find Submission
    print(f"Searching for {filename}...")
    cursor.execute(
        "SELECT id, user_id, word_id, file_path FROM submissions WHERE file_path LIKE ?",
        (f"%{filename}",),
    )
    sub = cursor.fetchone()

    if sub:
        sub_id, user_id, word_id, _ = sub
        print(f"Found Submission ID: {sub_id}")
        print(f"User ID: {user_id}")
        print(f"Word ID: {word_id}")

        # 2. Find Word
        cursor.execute("SELECT text, audio_path FROM words WHERE id = ?", (word_id,))
        word = cursor.fetchone()
        if word:
            text, audio_path = word
            print(f"Word: {text}")
            print(f"Reference Audio: {audio_path}")
        else:
            print("Word not found!")
    else:
        print("Submission not found in temp DB.")

    conn.close()


def dump_latest() -> None:
    db_path = "instance/temp_prod.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Latest 5 Submissions ---")
    cursor.execute(
        "SELECT id, user_id, word_id, file_path FROM submissions ORDER BY id DESC LIMIT 5"
    )
    rows = cursor.fetchall()

    for r in rows:
        print(r)

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dump_latest()
    else:
        query_submission(sys.argv[1])
