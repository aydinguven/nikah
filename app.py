from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from PIL import Image
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

def create_thumbnail(filepath, thumb_size=(300, 300)):
    """Create a thumbnail for the uploaded image"""
    thumb_path = filepath.replace('/uploads/', '/uploads/thumbs/')
    os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
    
    with Image.open(filepath) as img:
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        img.thumbnail(thumb_size)
        img.save(thumb_path, 'JPEG', quality=85)
    return os.path.basename(thumb_path)

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

        # Create thumbnail
        thumb_filename = create_thumbnail(filepath)
        
        # Save metadata
        metadata = {
            'filename': filename,
            'thumbnail': thumb_filename,
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

@app.route('/uploads/thumbs/<filename>')
def thumbnail_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbs'), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)