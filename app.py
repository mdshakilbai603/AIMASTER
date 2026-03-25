import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# MoviePy ভার্সন সমস্যা সমাধানের জন্য ডাইনামিক ইমপোর্ট
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

# প্রোজেক্টের ফোল্ডার সেটআপ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# হাগিং ফেস থেকে প্রয়োজনীয় ফাইল সেভ করা
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
                print(f"✅ {m['file']} Downloaded!")
            except: pass

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=install_models).start()

@app.get("/")
async def status():
    return {
        "status": "Online",
        "developer": "Shakil",
        "project": "AI MASTER PRO",
        "message": "Ready for action!"
    }

# ভিডিও প্রসেসিং এপিআই
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        unique_id = uuid.uuid4()
        input_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{file.filename}")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ভিডিও লোড এবং প্রসেস
        clip = VideoFileClip(input_path)
        output_filename = f"processed_{unique_id}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # ভিডিও রেন্ডারিং (libx264 ব্যবহার করা হয়েছে দ্রুত কাজের জন্য)
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close()

        return {"status": "success", "url": f"/outputs/{output_filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Render-এর জন্য রান কমান্ড
if __name__ == "__main__":
    import uvicorn
    # Render নিজে থেকে PORT এনভায়রনমেন্ট ভেরিয়েবল দেয়
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
