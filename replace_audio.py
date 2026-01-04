import os
import static_ffmpeg
static_ffmpeg.add_paths()
import requests
import json
from pydub import AudioSegment

# --- CONFIGURATION ---
TARGET_RATE = 16000   # 16kHz standard for ML/Pronunciation
TARGET_CHANNELS = 1   # Mono
TARGET_DB = -1.0      # Peak loudness

# The Golden 20 List
WORDS = [
    "bike", "bird", "boat", "book", "boy", 
    "cake", "call", "cat", "chair", "cow", 
    "cup", "dark", "ear", "green", "hot", 
    "moon", "red", "sit", "tour", "wait"
]

OUTPUT_DIR = "audio"

def standardize_audio(file_path):
    """
    Standardizes audio to 16kHz, Mono, -1.0dB Peak.
    Overwrites the original file.
    """
    try:
        # 1. Load Audio
        audio = AudioSegment.from_file(file_path)
        
        # 2. Resample (Fix Sample Rate)
        if audio.frame_rate != TARGET_RATE:
            audio = audio.set_frame_rate(TARGET_RATE)
        
        # 3. Downmix (Stereo -> Mono)
        if audio.channels != TARGET_CHANNELS:
            audio = audio.set_channels(TARGET_CHANNELS)
        
        # 4. Normalize Loudness (Peak Normalization)
        # Calculates gain needed to hit TARGET_DB
        change_in_dB = TARGET_DB - audio.max_dBFS
        audio = audio.apply_gain(change_in_dB)
        
        # 5. Overwrite File (Export as MP3 to match filename)
        # Using specific bitrate to ensure quality
        audio.export(file_path, format="mp3", bitrate="128k")
        print(f"   -> Standardized: 16kHz | Mono | -1.0dB")
        return True
        
    except Exception as e:
        print(f"   -> ⚠️ Standardization Failed: {e}")
        return False

def populate_words():
    # Only useful if you have an index.json, otherwise not used in main execution
    try:
        with open(os.path.join(OUTPUT_DIR, "index.json"), "r") as f:
            data = json.load(f)
            return data["words"]
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return []

def remove_old_audio():
    if os.path.exists(OUTPUT_DIR):
        print(f"--- Removing old audio files ---")
        for file in os.listdir(OUTPUT_DIR):
            if file.endswith(".mp3"):
                os.remove(os.path.join(OUTPUT_DIR, file))

def download_audio(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            phonetics = data[0].get("phonetics", [])
            audio_url = None
            
            # 1. Try to find a British/UK version first (matches your IPA)
            for p in phonetics:
                if "audio" in p and p["audio"]:
                    if "-uk" in p["audio"] or "-gb" in p["audio"]:
                        audio_url = p["audio"]
                        break
            
            # 2. If no UK, take any available audio
            if not audio_url:
                for p in phonetics:
                    if "audio" in p and p["audio"]:
                        audio_url = p["audio"]
                        break
            
            if audio_url:
                # Fix Protocol if missing (API sometimes returns //ssl...)
                if audio_url.startswith("//"):
                    audio_url = "https:" + audio_url
                
                # Download
                print(f"Downloading {word} from {audio_url}...")
                doc = requests.get(audio_url)
                file_path = f"{OUTPUT_DIR}/{word}.mp3"
                
                with open(file_path, 'wb') as f:
                    f.write(doc.content)
                
                # --- APPLY STANDARDIZATION ---
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

    populate_words()
        
    print(f"--- Starting Download & Processing for {len(WORDS)} words ---")
    count = 0
    for w in WORDS:
        if download_audio(w):
            count += 1
    print(f"--- Finished. Processed {count}/{len(WORDS)} files. ---")