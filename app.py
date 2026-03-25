import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# MoviePy v2.0+ এবং পুরাতন ভার্সন দুটোর জন্যই ফিক্স
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

app = FastAPI()

# ব্রাউজার পারমিশন (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ডিরেক্টরি সেটআপ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# ফোল্ডার তৈরি নিশ্চিত করা
for folder in [UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# আউটপুট ফাইল এবং স্ট্যাটিক ফাইল সার্ভ করা
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# --- ১. মূল ওয়েবসাইট (Interface) লোড করার রুট ---
@app.get("/")
async def serve_home():
    # আপনার ফাইলটি templates ফোল্ডারের ভেতর আছে
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # ব্যাকআপ: মেইন ডিরেক্টরি চেক
    fallback_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(fallback_path):
        return FileResponse(fallback_path)
        
    return {"error": "index.html পাওয়া যায়নি। templates ফোল্ডার চেক করুন।"}

# --- ২. ভিডিও প্রসেসিং এপিআই (রিয়েল কাজ করার জন্য) ---
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        unique_id = uuid.uuid4()
        file_ext = file.filename.split(".")[-1]
        input_path = os.path.join(UPLOAD_DIR, f"{unique_id}.{file_ext}")
        
        # ফাইল সেভ করা
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ভিডিও এডিটিং লজিক (ক্যাপকাটের মতো রেন্ডারিং)
        clip = VideoFileClip(input_path)
        output_name = f"shakil_pro_{unique_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        # ভিডিও রেন্ডার করা (fast preset ব্যবহার করা হয়েছে দ্রুততার জন্য)
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
        clip.close()

        # রিয়েল ভিডিও লিঙ্ক পাঠানো
        return {"status": "success", "url": f"/outputs/{output_name}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Render পোর্ট বাইন্ডিং (Status 127 ফিক্স)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
