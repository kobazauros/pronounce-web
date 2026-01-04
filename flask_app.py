import os
from flask import Flask, request, jsonify, send_from_directory
from pydub import AudioSegment

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'student_recordings'
AUDIO_FOLDER = 'audio'  # Where your example files live
TARGET_RATE = 16000     # 16kHz
TARGET_CHANNELS = 1     # Mono
TARGET_DB = -1.0        # Peak Loudness

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def standardize_and_save(file_storage, save_path):
    """
    Reads an uploaded file (in memory), enforces standards, 
    and saves it to disk as MP3.
    """
    try:
        # 1. Load from the uploaded file object
        audio = AudioSegment.from_file(file_storage)

        # 2. Resample (Force 16kHz)
        if audio.frame_rate != TARGET_RATE:
            audio = audio.set_frame_rate(TARGET_RATE)

        # 3. Downmix (Force Mono)
        if audio.channels != TARGET_CHANNELS:
            audio = audio.set_channels(TARGET_CHANNELS)

        # 4. Normalize Loudness (Peak Normalization to -1.0 dB)
        # Check for silence to avoid division by zero errors
        if audio.max_dBFS > -90:
            change_in_dB = TARGET_DB - audio.max_dBFS
            audio = audio.apply_gain(change_in_dB)

        # 5. Export
        # We save as MP3 to match the extension sent by script.js
        audio.export(save_path, format="mp3", bitrate="128k")
        
        # Log for debugging
        print(f"✅ Saved & Standardized: {save_path} | {TARGET_RATE}Hz")
        return True

    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        return False

@app.route('/')
def index():
    return "Pronunciation App Backend is Running."

# Route to serve the frontend (if you are serving static files from here)
# If you just use this for API, you might not need this.
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Route to serve the "Example" audio files
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    student_id = request.form.get('studentId', 'unknown')
    word = request.form.get('word', 'unknown')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Construct a safe filename: "ID-WORD.mp3"
    # script.js sends "sid-word.mp3", so we can use file.filename or build it manually
    filename = f"{student_id}-{word}.mp3"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # --- THE CORE LOGIC ---
    success = standardize_and_save(file, save_path)
    
    if success:
        return jsonify({"message": f"Saved {filename} successfully"}), 200
    else:
        return jsonify({"error": "Audio processing failed"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)