import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import edge_tts

app = Flask(__name__)

# Render-এর জন্য স্টোরেজ সেটআপ
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    uploaded = []
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            uploaded.append(filename)
    return jsonify({'status': 'success', 'uploaded': uploaded})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Auto & Manual Dubbing API
@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    data = request.get_json()
    text = data.get('text', '')
    gender = data.get('gender', 'female') # 'male' বা 'female' বেছে নেওয়া
    
    # ছেলে ও মেয়ের জন্য প্রিমিয়াম বাংলা ভয়েস
    voice = "bn-BD-PradeepNeural" if gender == "male" else "bn-BD-NabanitaNeural"
    
    try:
        output_name = f"dub_{os.urandom(3).hex()}.mp3"
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
