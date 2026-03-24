import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from moviepy.editor import VideoFileClip

app = FastAPI()

# CORS সেটিংস
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

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# মডেল অটো-ইন্সটলার
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

@app.get("/")
async def root():
    return {"message": "AI MASTER PRO is running, Shakil!"}

# Render-এর জন্য ডাইনামিক পোর্ট
if __name__ == "__main__":
    import uvicorn
    # Render অটোমেটিক PORT এনভায়রনমেন্ট ভেরিয়েবল দেয়
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
