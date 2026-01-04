import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Find the absolute path to the folder containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Join it with 'submissions' so it always ends up in /home/username/mysite/submissions
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'submissions')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('audio', filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    student_id = request.form.get('studentId', 'unknown')
    student_name = request.form.get('studentName', 'unknown')
    word = request.form.get('word', 'unknown')

    # NEW: Get the test type (Default to 'pre' if missing)
    test_type = request.form.get('testType', 'pre')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    safe_name = "".join([c for c in student_name if c.isalnum() or c in (' ', '_')]).replace(" ", "_")
    filename = f"{student_id}_{safe_name}_{word}.mp3"

    # NEW: Determine folder based on selection
    if test_type == 'post':
        sub_folder = 'post'
    else:
        sub_folder = 'pre'

    # Create the specific subfolder (e.g., submissions/pre)
    target_dir = os.path.join(UPLOAD_FOLDER, sub_folder)
    os.makedirs(target_dir, exist_ok=True)

    # Save to that new folder
    save_path = os.path.join(target_dir, filename)

    response = None
    status_code = 200

    try:
        file.save(save_path)
        print(f"Saved: {filename} to {save_path}")
        response = jsonify({"message": f"Saved {filename}"})
    except Exception as e:
        print(f"Error saving file: {e}")
        response = jsonify({"error": "Failed to save file"})
        status_code = 500

    return response, status_code

if __name__ == '__main__':
    app.run(debug=True, port=5000)