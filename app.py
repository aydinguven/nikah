from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from datetime import datetime
import json
import ssl

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['photo']
    uploader_name = request.form.get('uploaderName', 'Anonymous')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Create a unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the file
        file.save(filepath)

        # Save metadata
        metadata = {
            'filename': filename,
            'uploader': uploader_name,
            'timestamp': timestamp,
            'originalName': file.filename
        }

        metadata_path = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
        try:
            with open(metadata_path, 'r') as f:
                existing_metadata = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_metadata = []

        existing_metadata.append(metadata)
        with open(metadata_path, 'w') as f:
            json.dump(existing_metadata, f)

        return jsonify({'success': True, 'filename': filename}), 200

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/api/photos', methods=['GET'])
def get_photos():
    metadata_path = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return jsonify(metadata)
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)