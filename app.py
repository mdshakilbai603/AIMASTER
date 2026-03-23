import os
import asyncio
import uuid
import requests  # HeyGen API-এর জন্য প্রয়োজন
from flask import Flask, render_template, request, jsonify, send_from_directory
import edge_tts

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get("RENDER_DISK_PATH", "/tmp/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# *** HeyGen API Configuration (এখানে আপনার API Key দিতে হবে) ***
HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "YOUR_ACTUAL_HEYGEN_API_KEY_HERE")
HEYGEN_API_URL = "https://api.heygen.com/v1/lip_sync.create"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    uploaded_assets = []
    for file in files:
        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            unique_name = f"{uuid.uuid4().hex}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            uploaded_assets.append({'name': file.filename, 'url': f'/uploads/{unique_name}', 'unique_name': unique_name})
    return jsonify({'status': 'success', 'files': uploaded_assets})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Advanced Dubbing + Lip-Sync Engine
@app.route('/api/generate-dub-sync', methods=['POST'])
def generate_dub_sync():
    data = request.get_json()
    text = data.get('text', '')
    gender = data.get('gender', 'female')
    video_filename = data.get('video_filename', '') # মূল ভিডিও ফাইলের নাম
    
    if not text or not video_filename:
        return jsonify({'error': 'Missing text or video'}), 400
        
    voice = "bn-BD-PradeepNeural" if gender == "male" else "bn-BD-NabanitaNeural"
    
    try:
        # Step 1: Generate TTS Audio (Edge-TTS)
        dub_name = f"dub_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], dub_name)
        communicate = edge_tts.Communicate(text, voice)
        asyncio.run(communicate.save(audio_path))
        
        # Step 2: Trigger HeyGen Lip-Sync (AI Magic)
        # ভিডিও এবং অডিওর URL তৈরি করা (HeyGen-এর অ্যাক্সেস প্রয়োজন)
        # Render-এ থাকলে এটি পাবলিক URL হতে হবে। লোকালহোস্টে কাজ করবে না।
        base_url = request.host_url.rstrip('/') 
        video_url = f"{base_url}/uploads/{video_filename}"
        audio_url = f"{base_url}/uploads/{dub_name}"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": HEYGEN_API_KEY
        }
        payload = {
            "video_url": video_url,
            "audio_url": audio_url,
            "caption": False # ক্যাপশন অফ রাখা হলো নাটকের জন্য
        }

        # HeyGen-এ লিপ-সিঙ্ক টাস্ক পাঠানো
        response = requests.post(HEYGEN_API_URL, json=payload, headers=headers)
        result = response.json()

        if response.status_code == 200 and result.get('status') == 'success':
            # HeyGen একটি Task ID দিবে। লিপ-সিঙ্ক হতে সময় লাগে।
            # আমরা টাস্ক আইডি পাঠাবো ফ্রন্টএন্ডে, ফ্রন্টএন্ড কিছুক্ষণ পর পর চেক করবে।
            return jsonify({
                'status': 'processing',
                'task_id': result['data']['task_id'],
                'audio_url': f'/uploads/{dub_name}', # ব্যাকআপ অডিও
                'message': 'AI Lip-Syncing started...'
            })
        else:
            # HeyGen ফেল করলে শুধু অডিও সিঙ্ক হবে (লিপ-সিঙ্ক ছাড়া)
            return jsonify({
                'status': 'fallback_audio_only',
                'audio_url': f'/uploads/{dub_name}',
                'message': 'Lip-Sync failed, using audio only.'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HeyGen টাস্ক স্ট্যাটাস চেক করার এপিআই
@app.route('/api/check-sync-status/<task_id>', methods=['GET'])
def check_sync_status(task_id):
    headers = {
        "accept": "application/json",
        "x-api-key": HEYGEN_API_KEY
    }
    # HeyGen-এর টাস্ক স্ট্যাটাস এপিআই URL (আপনার API ভার্সন অনুযায়ী পরিবর্তন হতে পারে)
    status_url = f"https://api.heygen.com/v1/lip_sync.get?task_id={task_id}"
    
    response = requests.get(status_url, headers=headers)
    result = response.json()
    
    if response.status_code == 200 and result.get('status') == 'success':
        task_data = result['data']
        if task_data['status'] == 'completed':
            return jsonify({
                'status': 'completed',
                'video_url': task_data['video_url'] # লিপ-সিঙ্ক করা ফাইনাল ভিডিও URL
            })
        elif task_data['status'] == 'failed':
            return jsonify({'status': 'failed', 'error': task_data.get('error')})
        else:
            return jsonify({'status': 'processing'})
    else:
        return jsonify({'status': 'error', 'message': 'Could not check status'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
