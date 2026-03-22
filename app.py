import os
import traceback
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==================== CONFIG ====================
# Render Disk Mount Path — Dashboard > Disks > Mount Path-এ যা লেখা আছে সেটা এখানে ব্যবহার করো
# সবচেয়ে নিরাপদ ও সাধারণ: '/data'
UPLOAD_FOLDER = '/data'

# Disk path initialization with safe handling
upload_folder_status = "Not initialized"
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    upload_folder_status = f"Upload folder OK: {UPLOAD_FOLDER}"
    print(upload_folder_status)
except PermissionError as e:
    upload_folder_status = f"Permission denied on {UPLOAD_FOLDER}: {e} → Using memory-only (temporary)"
    print(upload_folder_status)
    print("SOLUTION: Go to Render Dashboard → Disks → Add/Edit Disk → Mount Path must be exactly '/data'")
except Exception as e:
    upload_folder_status = f"Disk setup failed: {e}"
    print(upload_folder_status)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==================== Hugging Face TTS (Bengali) ====================
HF_READY = False
model = None
tokenizer = None
sampling_rate = None

try:
    from transformers import VitsModel, AutoTokenizer
    import torch
    import soundfile as sf

    print("Loading Hugging Face MMS-TTS-Bengali model...")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-ben")
    model = VitsModel.from_pretrained("facebook/mms-tts-ben")
    sampling_rate = model.config.sampling_rate
    HF_READY = True
    print("Hugging Face TTS model loaded successfully (CPU mode)")
except Exception as e:
    print(f"Hugging Face load failed: {e}")
    print("Requirements: transformers, torch, torchaudio, soundfile must be in requirements.txt")
    HF_READY = False

# ==================== ROUTES ====================

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
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)
            uploaded.append(filename)
        except Exception as save_err:
            print(f"Save failed for {filename}: {save_err}")

    return jsonify({'status': 'success', 'uploaded': uploaded})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/assets')
def get_assets():
    try:
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if not f.startswith('.')]
    except Exception as e:
        print(f"Cannot list directory {UPLOAD_FOLDER}: {e}")
        files = []

    assets = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        typ = 'file'
        if ext in ['.mp4', '.mov', '.webm', '.avi']: typ = 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']: typ = 'image'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']: typ = 'audio'

        assets.append({
            'name': f,
            'url': f'/uploads/{f}',
            'type': typ
        })
    return jsonify(assets)


@app.route('/api/generate-dub-hf', methods=['POST'])
def generate_dub_hf():
    if not HF_READY:
        return jsonify({'error': 'Hugging Face libraries or model not loaded'}), 503

    data = request.get_json()
    text = data.get('text', 'আপনার ডাবিং টেক্সট এখানে লিখুন')

    if not text.strip():
        return jsonify({'error': 'Text is empty'}), 400

    try:
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform

        audio_filename = f"dub_{hash(text)}.wav"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)

        sf.write(audio_path, output.squeeze().cpu().numpy(), samplerate=sampling_rate)

        return jsonify({
            'status': 'success',
            'audio_url': f'/uploads/{audio_filename}',
            'message': 'Hugging Face AI দিয়ে বাংলা ভয়েস তৈরি হয়েছে'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
