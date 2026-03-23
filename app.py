import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import edge_tts

app = Flask(__name__)

# Render-এর জন্য Safe Temporary Path
UPLOAD_FOLDER = os.environ.get("RENDER_DISK_PATH", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part'}), 400
    
    files = request.files.getlist('files')
    uploaded = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded.append(filename)
    return jsonify({'status': 'success', 'uploaded': uploaded})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/assets')
def get_assets():
    try:
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if not f.startswith('.')]
        assets = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            typ = 'video' if ext in ['.mp4', '.webm'] else 'image' if ext in ['.jpg', '.png'] else 'audio' if ext in ['.mp3', '.wav'] else 'file'
            assets.append({'name': f, 'url': f'/uploads/{f}', 'type': typ})
        return jsonify(assets)
    except:
        return jsonify([])

@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    data = request.get_json()
    text = data.get('text', '')
    if not text: return jsonify({'error': 'No text'}), 400
    
    try:
        voice = "bn-BD-NabanitaNeural" # ন্যাচারাল ফিমেইল ভয়েস 
        output_name = f"dub_{os.urandom(4).hex()}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], output_name)
        
        communicate = edge_tts.Communicate(text, voice)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(communicate.save(audio_path))
        loop.close()
        
        return jsonify({'status': 'success', 'audio_url': f'/uploads/{output_name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
