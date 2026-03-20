import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==================== Hugging Face + Disk Config ====================
UPLOAD_FOLDER = '/data'   # Render Disk Mount Path (ঠিক এটাই রাখো)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==================== Hugging Face TTS (Bengali) ====================
# অটো ইনস্টল হয় requirements.txt থেকে
try:
    from transformers import VitsModel, AutoTokenizer
    import torch
    import soundfile as sf
    HF_READY = True
except ImportError:
    HF_READY = False

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
        if ext in ['.mp4','.mov','.webm']: typ = 'video'
        elif ext in ['.jpg','.jpeg','.png','.gif']: typ = 'image'
        elif ext in ['.mp3','.wav']: typ = 'audio'
        assets.append({'name': f, 'url': f'/uploads/{f}', 'type': typ})
    return jsonify(assets)

# ==================== NEW: Hugging Face Bengali TTS ====================
@app.route('/api/generate-dub-hf', methods=['POST'])
def generate_dub_hf():
    if not HF_READY:
        return jsonify({'error': 'HF libraries not installed'}), 500

    data = request.json
    text = data.get('text', 'আপনার ডাবিং টেক্সট')

    try:
        tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-ben")
        model = VitsModel.from_pretrained("facebook/mms-tts-ben")

        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform

        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], "hf_dub.wav")
        sf.write(audio_path, output[0].numpy(), samplerate=model.config.sampling_rate)

        return jsonify({
            'status': 'success',
            'audio_url': '/uploads/hf_dub.wav',
            'message': 'Hugging Face AI দিয়ে Bengali Voice তৈরি হয়েছে!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
