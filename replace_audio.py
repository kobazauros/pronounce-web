import json
import os

import requests
import static_ffmpeg
from pydub import AudioSegment, silence

static_ffmpeg.add_paths()


# --- CONFIGURATION ---
TARGET_RATE = 16000  # 16kHz standard for ML/Pronunciation
TARGET_CHANNELS = 1  # Mono
TARGET_DB = -1.0  # Peak loudness

# The Golden 20 List (Fallback)
DEFAULT_WORDS = [
    "bike",
    "bird",
    "boat",
    "book",
    "boy",
    "cake",
    "call",
    "cat",
    "chair",
    "cow",
    "cup",
    "dark",
    "ear",
    "green",
    "hot",
    "moon",
    "red",
    "sit",
    "tour",
    "wait",
]

OUTPUT_DIR = "/static/audio"


def trim_audio(audio, silence_thresh=-50, chunk_size=10):
    """
    Trims silence from the beginning and end of the audio.
    """
    # Find start of audio
    start_trim = silence.detect_leading_silence(
        audio, silence_threshold=silence_thresh, chunk_size=chunk_size
    )

    # Find end of audio (by reversing it)
    end_trim = silence.detect_leading_silence(
        audio.reverse(), silence_threshold=silence_thresh, chunk_size=chunk_size
    )

    duration = len(audio)

    # Safety check: Don't trim if it removes everything
    if start_trim + end_trim >= duration:
        return audio

    return audio[start_trim : duration - end_trim]


def standardize_audio(file_path):
    """
    Standardizes audio:
    1. High-pass filter (remove DC offset/rumble)
    2. Trim Silence (remove clicks/dead air)
    3. Resample/Mono
    4. Normalize Loudness
    """
    try:
        # 1. Load Audio
        audio = AudioSegment.from_file(file_path)

        # 2. Trim Silence (Crucial for Dictionary API files)
        audio = trim_audio(audio)

        # 3. Resample (Fix Sample Rate)
        if audio.frame_rate != TARGET_RATE:
            audio = audio.set_frame_rate(TARGET_RATE)

        # 4. Downmix (Stereo -> Mono)
        if audio.channels != TARGET_CHANNELS:
            audio = audio.set_channels(TARGET_CHANNELS)

        # 5. Normalize Loudness (Peak Normalization)
        if audio.max_dBFS != -float("inf"):
            change_in_dB = TARGET_DB - audio.max_dBFS
            audio = audio.apply_gain(change_in_dB)

        # 6. Overwrite File
        audio.export(file_path, format="mp3", bitrate="128k")
        print("   -> Standardized: 16kHz | Mono | Trimmed | -1.0dB")
        return True

    except Exception as e:
        print(f"   -> ⚠️ Standardization Failed: {e}")
        return False


def load_words_from_json():
    json_path = os.path.join(OUTPUT_DIR, "index.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("words", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def remove_old_audio():
    if os.path.exists(OUTPUT_DIR):
        print("--- Removing old audio files ---")
        for file in os.listdir(OUTPUT_DIR):
            if file.endswith(".mp3"):
                os.remove(os.path.join(OUTPUT_DIR, file))


def download_audio(word_input):
    # Handle Dict vs String input
    if isinstance(word_input, dict):
        word = word_input.get("word")
    else:
        word = word_input

    if not word:
        return False

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"❌ API Error for {word}: {response.status_code}")
            return False

        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            phonetics = data[0].get("phonetics", [])
            audio_url = None

            # Priority: UK -> US -> Any
            for p in phonetics:
                if (
                    "audio" in p
                    and p["audio"]
                    and ("-uk" in p["audio"] or "-gb" in p["audio"])
                ):
                    audio_url = p["audio"]
                    break

            if not audio_url:
                for p in phonetics:
                    if "audio" in p and p["audio"]:
                        audio_url = p["audio"]
                        break

            if audio_url:
                if audio_url.startswith("//"):
                    audio_url = "https:" + audio_url
                print(f"Downloading {word}...", end=" ")
                doc = requests.get(audio_url)
                file_path = os.path.join(OUTPUT_DIR, f"{word}.mp3")

                with open(file_path, "wb") as f:
                    f.write(doc.content)

                standardize_audio(file_path)
                return True
            else:
                print(f"❌ No audio found for {word}")
                return False
        else:
            print(f"❌ Word not found: {word}")
            return False

    except Exception as e:
        print(f"❌ Error downloading {word}: {e}")
        return False


# Execution
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    remove_old_audio()

    words_to_process = load_words_from_json()

    if words_to_process:
        print(f"--- Loaded {len(words_to_process)} words from index.json ---")
    else:
        words_to_process = DEFAULT_WORDS
        print("--- Using default Golden 20 list ---")

    print("--- Starting Download & Processing ---")

    success_count = 0
    for w in words_to_process:
        if download_audio(w):
            success_count += 1

    print(f"--- Finished. Processed {success_count}/{len(words_to_process)} files. ---")
