import os
import requests
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip, AudioFileClip

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ডিরেক্টরি সেটআপ (সারা জীবনের জন্য সেভ রাখার ফোল্ডার)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models_storage") # এখানে মডেল সেভ থাকবে
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# --- ১. অটোমেটিক মডেল ডাউনলোডার (একবারই হবে, আজীবনের জন্য) ---
def download_model_once(repo_id, filename):
    local_path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(local_path):
        print(f"✅ Model '{filename}' already exists. Skipping download.")
        return local_path
    
    print(f"🚀 Downloading {filename} from Hugging Face... Please wait.")
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✨ {filename} saved successfully in {MODEL_DIR}")
        return local_path
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

# সার্ভার স্টার্ট হওয়ার সময় প্রয়োজনীয় মডেল ডাউনলোড হবে (উদাহরণস্বরূপ)
# @app.on_event("startup")
# def startup_event():
#     # এখানে আপনার প্রয়োজনীয় মডেলের Repo ID এবং ফাইলের নাম দিন
#     download_model_once("openai/whisper-large", "whisper_model.bin")

# --- ২. ভিডিও আপলোড ---
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    name = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"status": "success", "filename": name}

# --- ৩. এপিআই: মডেল ডাউনলোড ও ব্রাউজারে সেভ (আপনার রিকোয়েস্ট অনুযায়ী) ---
@app.get("/api/install-model")
async def install_model(repo: str, file: str):
    path = download_model_once(repo, file)
    if path:
        return FileResponse(path=path, filename=file, media_type='application/octet-stream')
    raise HTTPException(status_code=500, detail="Download failed")

# --- ৪. ফাইনাল ডাবিং ও এক্সপোর্ট ইঞ্জিন ---
@app.post("/api/process-final")
async def process_video(
    video_name: str = Form(...), 
    text: str = Form(...), 
    gender: str = Form(...)
):
    try:
        video_path = os.path.join(UPLOAD_DIR, video_name)
        output_video = f"final_{uuid.uuid4()}.mp4"
        final_path = os.path.join(OUTPUT_DIR, output_video)

        # ১. এখানে আপনার AI Voice জেনারেট হবে (মডেল ফোল্ডার থেকে ফাইল নিয়ে)
        # ২. লিপ-সিঙ্ক বা ডাবিং প্রসেস হবে
        
        # উদাহরণ: মুভিপাই দিয়ে অডিও-ভিডিও মার্জ
        clip = VideoFileClip(video_path)
        # clip.write_videofile(final_path) # প্রসেসিং লজিক এখানে আসবে

        return {"status": "success", "url": f"/outputs/{output_video}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    # সার্ভার রান করার কমান্ড
    uvicorn.run(app, host="0.0.0.0", port=8000)
