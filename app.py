import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from moviepy.editor import VideoFileClip, AudioFileClip

app = FastAPI()

# ব্রাউজার পারমিশন (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ফোল্ডার সেটআপ (আজীবনের জন্য সেভ রাখার জায়গা) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models")  # আপনার মডেল স্টোরেজ
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# --- ১. অটোমেটিক মডেল ইন্সটলার (একবারই হবে, সারা জীবন থাকবে) ---
def install_system_models():
    # এখানে আপনার ডাবিং বা লিপ-সিঙ্কের মেইন মডেলগুলোর লিস্ট দিন
    required_models = [
        {"repo": "guillaumekln/faster-whisper-large-v2", "file": "model.bin"},
        {"repo": "TencentARC/GFPGAN", "file": "GFPGANv1.4.pth"} # উদাহরণ
    ]
    
    for item in required_models:
        local_path = os.path.join(MODEL_DIR, item['file'])
        if not os.path.exists(local_path):
            print(f"🚀 Installing Model: {item['file']}...")
            url = f"https://huggingface.co/{item['repo']}/resolve/main/{item['file']}"
            try:
                with requests.get(url, stream=True) as r:
                    with open(local_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                print(f"✅ {item['file']} Installed Successfully.")
            except Exception as e:
                print(f"❌ Error: {e}")

# সার্ভার চালু হওয়ার সাথে সাথে ইন্সটল শুরু হবে
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=install_system_models)
    thread.start()

# --- ২. ব্রাউজার অটো-ডাউনলোড এপিআই ---
@app.get("/api/browser-install")
async def browser_install(filename: str):
    file_path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    return JSONResponse({"error": "ফাইলটি আগে সার্ভারে ইন্সটল হতে দিন।"})

# --- ৩. ভিডিও এডিটিং ও রিং এনিমেশন প্রসেস ---
@app.post("/api/final-render")
async def render_video(video_name: str = Form(...), text: str = Form(...)):
    try:
        input_path = os.path.join(UPLOAD_DIR, video_name)
        output_name = f"shakil_final_{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)

        # এখানে MoviePy দিয়ে আপনার রিং এনিমেশন বা লোগো ভিডিওতে যোগ করার কোড
        video = VideoFileClip(input_path)
        
        # আপনার স্পেশাল রিং এনিমেশন লজিক (সিমুলেশন)
        print(f"Adding Ring Animation for {text}...")
        
        # ফাইনাল ভিডিও সেভ
        video.write_videofile(output_path, codec="libx264")
        
        return {"status": "success", "video_url": f"/outputs/{output_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ৪. ভিডিও আপলোড ---
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    name = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
