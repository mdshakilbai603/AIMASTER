import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import edge_tts

app = Flask(__name__)

# Render Disk mount path — অবশ্যই Dashboard > Disks > Mount Path-এ /data করো
UPLOAD_FOLDER = '/data'

# Disk safe initialization
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"Upload folder ready: {UPLOAD_FOLDER}")
except Exception as e:
    print(f"Disk warning: {e} — continuing without persistent storage")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files'}), 400
    
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
    except:
        files = []
    
    assets = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        typ = 'file'
        if ext in ['.mp4', '.mov', '.webm']: typ = 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']: typ = 'image'
        elif ext in ['.mp3', '.wav']: typ = 'audio'
        assets.append({'name': f, 'url': f'/uploads/{f}', 'type': typ})
    
    return jsonify(assets)

# Bengali TTS using edge-tts (very lightweight)
@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    data = request.get_json()
    text = data.get('text', 'আপনার ডাবিং টেক্সট এখানে লিখুন')
    
    try:
        voice = "bn-BD-NabanitaNeural"  # Female Bengali (very natural)
        communicate = edge_tts.Communicate(text, voice)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], "dub_output.mp3")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(communicate.save(audio_path))
        loop.close()
        
        return jsonify({
            'status': 'success',
            'audio_url': '/uploads/dub_output.mp3',
            'message': 'Bengali voice generated using Microsoft Edge TTS'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
