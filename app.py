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

# CORS সেটিংস যাতে index.html থেকে রিকোয়েস্ট কাজ করে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- পাথ এবং ডিরেক্টরি সেটআপ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Render বা হাগিং ফেসের জন্য পারমানেন্ট স্টোরেজ পাথ
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# স্ট্যাটিক ফাইল এক্সেস
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
                    with open(dest, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                print(f"✅ {m['file']} saved forever.")
            except:
                print(f"❌ Failed to download {m['file']}")

# ব্যাকগ্রাউন্ডে মডেল ডাউনলোড শুরু করা
@app.on_event("startup")
async def startup_event():
    threading.Thread(target=install_models).start()

# --- ২. ভিডিও আপলোড ---
@app.post("/upload")
async def upload_video(files: list[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, unique_name)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append({
            "url": f"/uploads/{unique_name}", 
            "original_name": file.filename
        })
    return {"status": "success", "files": uploaded_files}

# --- ৩. ড্রামা ডাবিং এপিআই (আপনার ইন্টারফেসের জন্য) ---
@app.post("/api/generate-dub")
async def generate_dub(data: dict):
    text = data.get("text")
    gender = data.get("gender")
    
    # এখানে আপনার ভয়েস জেনারেশন মডেল কাজ করবে
    # আপাতত একটি ডামি আউটপুট দেওয়া হলো যা আপনার UI-তে অডিও চালাবে
    output_audio = f"dub_{uuid.uuid4()}.mp3"
    # voice_model.generate(text, gender, save_to=os.path.join(OUTPUT_DIR, output_audio))
    
    return {
        "status": "success", 
        "audio_url": f"/outputs/{output_audio}"
    }

# --- ৪. রিং এনিমেশন ও ফাইনাল এক্সপোর্ট ---
@app.post("/api/export")
async def export_video(video_filename: str = Form(...)):
    try:
        v_path = os.path.join(UPLOAD_DIR, video_filename)
        output_name = f"shakil_final_{uuid.uuid4()}.mp4"
        final_path = os.path.join(OUTPUT_DIR, output_name)

        # MoviePy দিয়ে রিং বা লোগো যোগ করা
        clip = VideoFileClip(v_path)
        # clip = add_ring_animation(clip) # আপনার কাস্টম লজিক
        clip.write_videofile(final_path, codec="libx264")

        return {"status": "success", "download_url": f"/outputs/{output_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Render-এর সমস্যার সমাধান: সরাসরি সার্ভার রান করা
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
