import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ফোল্ডার সেটআপ
UPLOAD_FOLDER = 'uploads'
DUB_FOLDER = 'dubs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DUB_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['files']
    if file.filename == '':
        return jsonify({"error": "No filename"}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({
        "uploaded": [{"name": file.filename, "url": f"/uploads/{file.filename}"}]
    })

@app.route('/api/generate-dub', methods=['POST'])
def generate_dub():
    # এখানে ElevenLabs এর ডামি রেসপন্স দেওয়া হচ্ছে
    # আপনি আপনার ElevenLabs API Key ব্যবহার করে রিয়েল ভয়েস জেনারেট করতে পারবেন
    dub_id = os.urandom(4).hex()
    return jsonify({
        "status": "success",
        "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", # ডামি অডিও
        "id": dub_id
    })

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
