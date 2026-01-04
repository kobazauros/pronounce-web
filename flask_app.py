import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'student_recordings'
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
    # 1. Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    student_id = request.form.get('studentId', 'unknown')
    student_name = request.form.get('studentName', 'unknown')
    word = request.form.get('word', 'unknown')
    
    # 2. Check if user selected a file
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 3. Save the file (Logic unindented to ensure a return value)
    safe_name = "".join([c for c in student_name if c.isalnum() or c in (' ', '_')]).replace(" ", "_")
    filename = f"{student_id}_{safe_name}_{word}.mp3"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        file.save(save_path)
        print(f"Saved: {filename}")
        return jsonify({"message": f"Saved {filename}"}), 200
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({"error": "Failed to save file"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)