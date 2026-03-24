import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from moviepy.editor import VideoFileClip

app = FastAPI()

# CORS সেটিংস (যাতে আপনার HTML/ব্রাউজার থেকে API কল করা যায়)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- পাথ এবং ডিরেক্টরি সেটআপ (আজীবনের জন্য স্টোরেজ) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# স্ট্যাটিক ফাইল এক্সেস (ভিডিও/অডিও ব্রাউজারে দেখানোর জন্য)
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# --- ১. অটোমেটিক মডেল ইন্সটলার (একবারই হবে) ---
def install_models():
    # আপনার প্রয়োজনীয় মডেলগুলোর লিস্ট এখানে দিন
    models_to_fetch = [
        {"repo": "openai/whisper-base", "file": "model.bin"},
        {"repo": "TencentARC/GFPGAN", "file": "GFPGANv1.4.pth"}
    ]
    
    for m in models_to_fetch:
        dest = os.path.join(MODEL_DIR, m['file'])
        if not os.path.exists(dest):
            print(f"🚀 Installing {m['file']} for the first time...")
            url = f"https://huggingface.co/{m['repo']}/resolve/main/{m['file']}"
            try:
                with requests.get(url, stream=True) as r:
                    if r.status_code == 200:
                        with open(dest, 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                        print(f"✅ {m['file']} saved forever in {MODEL_DIR}.")
                    else:
                        print(f"❌ Failed to find {m['file']} on Hugging Face.")
            except Exception as e:
                print(f"❌ Download error for {m['file']}: {e}")

# ব্যাকগ্রাউন্ডে মডেল ডাউনলোড শুরু করা
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=install_models)
    thread.start()

# --- ২. ব্রাউজার অটো-ডাউনলোড এপিআই ---
@app.get("/api/install-model")
async def install_model_browser(filename: str):
    file_path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    return JSONResponse({"error": "ফাইলটি সার্ভারে নেই বা এখনও ডাউনলোড হচ্ছে।"})

# --- ৩. ভিডিও আপলোড ---
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": unique_name}

# --- ৪. ডাবিং এপিআই ---
@app.post("/api/generate-dub")
async def generate_dub(text: str = Form(...), gender: str = Form(...)):
    # এখানে আপনার ভয়েস জেনারেশন মডেল কাজ করবে
    output_audio = f"dub_{uuid.uuid4()}.mp3"
    
    # আপাতত ডামি রেসপন্স
    return {
        "status": "success", 
        "audio_url": f"/outputs/{output_audio}"
    }

# --- ৫. রিং এনিমেশন ও ফাইনাল এক্সপোর্ট ---
@app.post("/api/export")
async def export_video(video_filename: str = Form(...)):
    try:
        v_path = os.path.join(UPLOAD_DIR, video_filename)
        output_name = f"shakil_final_{uuid.uuid4()}.mp4"
        final_path = os.path.join(OUTPUT_DIR, output_name)

        # MoviePy দিয়ে ভিডিও লোড এবং প্রসেস করা
        clip = VideoFileClip(v_path)
        
        # (ভবিষ্যতে এখানে আপনার এনিমেশন যুক্ত হবে)
        
        # ফাইনাল ভিডিও রেন্ডার
        clip.write_videofile(final_path, codec="libx264", audio_codec="aac")

        return {"status": "success", "download_url": f"/outputs/{output_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Render-এর জন্য ডাইনামিক পোর্ট কনফিগারেশন ---
if __name__ == "__main__":
    import uvicorn
    # Render নিজে থেকে একটি পোর্ট দেয়, সেটা ব্যবহার করার জন্য এই লাইন:
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
