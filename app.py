import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# MoviePy v2.0+ ফিক্স
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

app = FastAPI()

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

# গুরুত্বপূর্ণ: এটি আপনার আউটপুট এবং স্ট্যাটিক ফাইল দেখাবে
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# ১. মূল ওয়েবসাইট (HTML) দেখানোর জন্য এই রুটটি দরকার
@app.get("/")
async def serve_home():
    # আপনার ফাইলটির নাম যদি index.html হয় এবং সেটি মেইন ফোল্ডারে থাকে
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "index.html ফাইলটি খুঁজে পাওয়া যায়নি! সেটি আপলোড করুন।"}

# ২. মডেল অটো-ইন্সটলার
def install_models():
    models = [{"repo": "openai/whisper-base", "file": "model.bin"}]
    for m in models:
        dest = os.path.join(MODEL_DIR, m['file'])
        if not os.path.exists(dest):
            url = f"https://huggingface.co/{m['repo']}/resolve/main/{m['file']}"
            try:
                r = requests.get(url, stream=True)
                with open(dest, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            except: pass

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=install_models).start()

# ৩. ভিডিও প্রসেসিং এপিআই
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{file_ext}"
        input_path = os.path.join(UPLOAD_DIR, unique_name)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        clip = VideoFileClip(input_path)
        output_name = f"shakil_final_{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        # এখানে আপনার রিং এনিমেশন যোগ করার কোড বসবে
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()

        return {"status": "success", "url": f"/outputs/{output_name}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
