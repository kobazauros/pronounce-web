# pyright: strict
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import bs4
import requests

DEFAULT_REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
LINK_PREFIX = "https://dictionary.cambridge.org"


def get_word_data(
    word: str,
    request_headers: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Fetches the British English pronunciation (IPA and MP3) for a given word
    from the Cambridge Dictionary.

    Args:
        word (str): The word to look up.
        request_headers (dict, optional): Headers for the HTTP request.
        timeout (float, optional): Request timeout in seconds.

    Returns:
        A tuple containing:
        - str or None: The IPA transcription string (e.g., "/ɪə(r)/").
        - bytes or None: The content of the MP3 audio file.
    """
    if request_headers is None:
        request_headers = DEFAULT_REQUESTS_HEADERS

    link = f"{LINK_PREFIX}/dictionary/english/{word}"

    transcription = None
    audio_bytes = None

    try:
        time.sleep(1)
        page = requests.get(link, headers=request_headers, timeout=timeout)
        page.raise_for_status()

        soup = bs4.BeautifulSoup(page.content, "html.parser")
        uk_pron_block = soup.find("span", class_="uk dpron-i")

        if not uk_pron_block:
            return None, None

        # 1. Get the IPA transcription.
        ipa_span = uk_pron_block.find("span", class_="ipa")
        if ipa_span:
            final_ipa_parts: List[str] = []
            for content in ipa_span.contents:
                if isinstance(content, str):
                    final_ipa_parts.append(content.strip())
                elif isinstance(content, bs4.Tag):
                    classes = content.attrs.get("class", [])
                    if (
                        content.name == "span"
                        and isinstance(classes, list)
                        and "sp" in classes
                        and "dsp" in classes
                    ):
                        final_ipa_parts.append(f"({content.text.strip()})")

            transcription = f"/{''.join(final_ipa_parts)}/"

        # 2. Get the MP3 file bytes.
        audio_source = uk_pron_block.find("source", type="audio/mpeg")
        if audio_source and audio_source.get("src"):
            mp3_src = audio_source.get("src")
            mp3_url = f"{LINK_PREFIX}{mp3_src}"

            try:
                mp3_response = requests.get(
                    mp3_url, headers=request_headers, timeout=timeout
                )
                mp3_response.raise_for_status()
                audio_bytes = mp3_response.content

            except requests.exceptions.RequestException as e:
                # Log or handle MP3 download error if needed, but don't stop.
                print(f"Warning: Could not download MP3 for '{word}': {e}")

    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch page for '{word}': {e}")
        return None, None

    return transcription, audio_bytes


def update_word_list(limit: int = 20) -> int:
    """
    Populates the database with the thesis word list.
    """
    from models import Word, db

    # Thesis Word List (20 words)
    # 10 Monophthongs, 8 Diphthongs, 2 Extras?
    # Based on user's earlier context:
    words = [
        "beat",
        "bit",
        "bet",
        "bat",
        "ask",
        "box",
        "off",
        "sort",
        "put",
        "pool",
        "cup",
        "bird",
        "about",
        "day",
        "go",
        "high",
        "how",
        "boy",
        "ear",
        "air",
        "sure",
    ]
    # Limit to 'limit'
    words = words[:limit]

    count = 0
    for i, w_text in enumerate(words):
        if not Word.query.filter_by(text=w_text).first():
            print(f"Fetching {w_text}...")
            ipa, audio = get_word_data(w_text)

            # Save Audio locally
            audio_path = None
            if audio:
                # Ensure static/audio exists
                # Assuming current working dir is app root
                save_dir = "static/audio"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                filename = f"{w_text}.mp3"
                full_path = os.path.join(save_dir, filename)
                with open(full_path, "wb") as f:
                    f.write(audio)
                audio_path = filename  # Store relative to static/audio or serving logic

            w = Word(text=w_text, sequence_order=i + 1, ipa=ipa, audio_path=audio_path)
            db.session.add(w)
            count += 1
            print(f"Added {w_text}")

    db.session.commit()
    return count


if __name__ == "__main__":
    """
    Example usage when run as a standalone script.
    """
    word_to_find = "ear"
    print(f"--- Fetching data for '{word_to_find}' ---")

    ipa, audio = get_word_data(word_to_find)

    if ipa:
        print(f"IPA: {ipa}")
    else:
        print("IPA not found.")

    if audio:
        save_location = f"{word_to_find}.mp3"
        try:
            with open(save_location, "wb") as f:
                f.write(audio)
            print(f"MP3 file saved to: {save_location}")
        except IOError as e:
            print(f"Error saving MP3 file: {e}")
    else:
        print("Audio not found.")
