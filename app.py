import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# MoviePy v2.0+ এর জন্য নতুন ইমপোর্ট সিস্টেম
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

# পাথ সেটআপ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# হাগিং ফেস থেকে মডেল অটো-সেভ
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
                print(f"✅ {m['file']} Saved!")
            except: pass

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=install_models).start()

@app.get("/")
async def home():
    return {"status": "Online", "owner": "Shakil", "project": "AI MASTER PRO"}

# ভিডিও প্রসেসিং
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        file_ext = file.filename.split(".")[-1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ভিডিও লোড করা (এরর হ্যান্ডেল সহ)
        clip = VideoFileClip(input_path)
        output_name = f"final_{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        # ভিডিও রেন্ডার
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        clip.close() # মেমোরি খালি করা

        return {"status": "success", "url": f"/outputs/{output_name}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
