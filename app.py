import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ১. অ্যাপ কনফিগারেশন
app = Flask(__name__, static_folder='.')
CORS(app) # এটি ডোমেইন এরর ফিক্স করবে

# ২. ফোল্ডার সেটআপ (ভিডিও এবং ডাবিং ফাইল জমানোর জন্য)
UPLOAD_FOLDER = 'uploads'
DUB_FOLDER = 'dubs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DUB_FOLDER, exist_ok=True)

# ৩. ElevenLabs কনফিগারেশন (আপনার এপিআই কি এখানে বসাবেন)
# এপিআই কি না থাকলে ডামি মোড কাজ করবে
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY"

@app.route('/')
def serve_index():
    """মূল ওয়েবসাইট (index.html) লোড করবে"""
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """ভিডিও বা অডিও ফাইল আপলোড করার রুট"""
    if 'files' not in request.files:
        return jsonify({"error": "কোনো ফাইল পাওয়া যায়নি"}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        uploaded_files.append({
            "original_name": filename,
            "url": f"/uploads/{filename}"
        })
    
    return jsonify({"status": "success", "files": uploaded_files})

@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    """ইলেভেন ল্যাবস এপিআই ব্যবহার করে ডাবিং তৈরি করবে"""
    data = request.json
    text = data.get('text')
    gender = data.get('gender', 'female') # ছেলে না মেয়ে কন্ঠ

    # ElevenLabs Voice IDs (এগুলো পরিবর্তন করা যায়)
    # বেলা (মেয়ে): EXAVITQu4vr4xnSDxMaL, জশ (ছেলে): pNInz6obpgDQGcFmaJgB
    voice_id = "EXAVITQu4vr4xnSDxMaL" if gender == "female" else "pNInz6obpgDQGcFmaJgB"

    # আপনি যদি ElevenLabs API Key না বসান, তবে এটি একটি ডামি অডিও রিটার্ন করবে
    if ELEVENLABS_API_KEY == "YOUR_ELEVENLABS_API_KEY":
        return jsonify({
            "status": "success", 
            "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "message": "Demo mode: Please add ElevenLabs API Key in app.py"
        })

    # ElevenLabs API Call
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            dub_filename = f"dub_{os.urandom(4).hex()}.mp3"
            dub_path = os.path.join(DUB_FOLDER, dub_filename)
            with open(dub_path, "wb") as f:
                f.write(response.content)
            return jsonify({"status": "success", "audio_url": f"/dubs/{dub_filename}"})
        else:
            return jsonify({"status": "error", "message": "API call failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """সার্ভার থেকে ফাইল ডিলিট করার সিস্টেম"""
    try:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)
            return jsonify({"status": "deleted"})
        return jsonify({"status": "not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ৪. ফাইল সার্ভ করার রুটস
@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/dubs/<filename>')
def serve_dubs(filename):
    return send_from_directory(DUB_FOLDER, filename)

# ৫. রেন্ডার এর জন্য মেইন ফাংশন
if __name__ == '__main__':
    # রেন্ডার পোর্ট অটোমেটিক ডিটেক্ট করবে
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
