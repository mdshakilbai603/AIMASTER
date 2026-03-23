import os
import asyncio
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import edge_tts

app = Flask(__name__)

# Render বা অন্য প্ল্যাটফর্মে ফাইল সেভ করার জন্য সঠিক পাথ সেট করা
UPLOAD_FOLDER = os.environ.get("RENDER_DISK_PATH", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    # সরাসরি ইনডেক্স পেজ লোড হবে
    return render_template('index.html')

# সব ধরণের ফাইল আপলোড করার জন্য উন্নত লজিক
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'ফাইল পাওয়া যায়নি'}), 400
    
    files = request.files.getlist('files')
    uploaded_assets = []
    
    for file in files:
        if file.filename:
            # ফাইলের নামের সাথে ইউনিক আইডি যুক্ত করা যাতে ওভাররাইট না হয়
            filename = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(file_path)
            
            # ফাইলের ধরণ নির্ধারণ করা
            ext = os.path.splitext(filename)[1].lower()
            typ = 'video' if ext in ['.mp4', '.webm', '.mov'] else 'image' if ext in ['.jpg', '.png', '.jpeg'] else 'audio'
            
            uploaded_assets.append({
                'name': filename,
                'url': f'/uploads/{unique_name}',
                'type': typ
            })
    
    return jsonify({'status': 'success', 'uploaded': uploaded_assets})

# আপলোড করা ফাইলগুলো ব্রাউজারে দেখানোর জন্য
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# এসেট লিস্ট পাওয়ার জন্য API
@app.route('/api/assets')
def get_assets():
    try:
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if not f.startswith('.')]
        assets = []
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            typ = 'video' if ext in ['.mp4', '.webm'] else 'image' if ext in ['.jpg', '.png'] else 'audio'
            assets.append({'name': f, 'url': f'/uploads/{f}', 'type': typ})
        return jsonify(assets)
    except Exception as e:
        return jsonify([])

# বাংলা ডাবিং জেনারেটর (Edge-TTS ব্যবহার করে)
@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    data = request.get_json()
    text = data.get('text', '')
    gender = data.get('gender', 'female') 
    
    # ছেলে বা মেয়ের ভয়েস সিলেকশন
    voice = "bn-BD-PradeepNeural" if gender == "male" else "bn-BD-NabanitaNeural"
    
    try:
        unique_audio = f"dub_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_audio)
        
        communicate = edge_tts.Communicate(text, voice)
        
        # Asyncio লুপ ম্যানেজমেন্ট
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(communicate.save(audio_path))
        loop.close()
        
        return jsonify({
            'status': 'success',
            'audio_url': f'/uploads/{unique_audio}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # পোর্ট অটো-ডিটেকশন
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
