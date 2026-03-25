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
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# আউটপুট ফাইল সার্ভ করা
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# --- ১. মূল ওয়েবসাইট (Interface) দেখানোর রুট ---
@app.get("/")
async def serve_home():
    # যেহেতু আপনার index.html ফাইলটি 'templates' ফোল্ডারের ভেতরে
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    # ব্যাকআপ হিসেবে মেইন ডিরেক্টরি চেক
    fallback_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(fallback_path):
        return FileResponse(fallback_path)
        
    return {"error": "index.html found nowhere. Please check folder structure."}

# --- ২. মডেল অটো-ইন্সটলার ---
def install_models():
    models = [{"repo": "openai/whisper-base", "file": "model.bin"}]
    for m in models:
        dest = os.path.join(MODEL_DIR, m['file'])
        if not os.path.exists(dest):
            url = f"https://huggingface.co/{m['repo']}/resolve/main/{m['file']}"
            try:
                with requests.get(url, stream=True) as r:
                    with open(dest, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            except: pass

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=install_models).start()

# --- ৩. ভিডিও প্রসেসিং এপিআই ---
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        unique_id = uuid.uuid4()
        file_ext = file.filename.split(".")[-1]
        input_path = os.path.join(UPLOAD_DIR, f"{unique_id}.{file_ext}")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ভিডিও লোড ও প্রসেস
        clip = VideoFileClip(input_path)
        output_name = f"shakil_final_{unique_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        # ডিফল্ট রেন্ডারিং
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()

        return {"status": "success", "url": f"/outputs/{output_name}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Render পোর্ট বাইন্ডিং
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
