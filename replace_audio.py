import os
import requests
import json

# The Golden 20 List
WORDS = [
    "bike", "bird", "boat", "book", "boy", 
    "cake", "call", "cat", "chair", "cow", 
    "cup", "dark", "ear", "green", "hot", 
    "moon", "red", "sit", "tour", "wait"
]

OUTPUT_DIR = "audio"

def populate_words():
    with open(OUTPUT_DIR + "index.json", "r") as f:
        data = json.load(f)
        return data["words"]

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
                with open(f"{OUTPUT_DIR}/{word}.mp3", 'wb') as f:
                    f.write(doc.content)
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
        
    print(f"--- Starting Download for {len(WORDS)} words ---")
    count = 0
    for w in WORDS:
        if download_audio(w):
            count += 1
    print(f"--- Finished. Downloaded {count}/{len(WORDS)} files. ---")