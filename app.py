import os
import requests
import uuid
import shutil
import threading
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from moviepy.editor import VideoFileClip

app = FastAPI()

# ১. ব্রাউজার এবং অন্যান্য প্ল্যাটফর্মের সাথে কানেক্ট করার পারমিশন
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ২. ডিরেক্টরি সেটআপ (আপনার ফাইলগুলো এখানে জমা থাকবে)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "shakil_models_storage")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# ফোল্ডারগুলো না থাকলে অটোমেটিক তৈরি হবে
for folder in [MODEL_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(folder, exist_ok=True)

# ৩. আউটপুট ফাইলগুলো অনলাইনে দেখার জন্য পাথ সেটআপ
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# ৪. অটোমেটিক মডেল ডাউনলোড (হাগিং ফেস থেকে আজীবনের জন্য)
def install_models():
    # এখানে আপনার প্রয়োজনীয় সব মডেলের লিঙ্ক দিতে পারেন
    models = [{"repo": "openai/whisper-base", "file": "model.bin"}]
    for m in models:
        dest = os.path.join(MODEL_DIR, m['file'])
        if not os.path.exists(dest):
            url = f"https://huggingface.co/{m['repo']}/resolve/main/{m['file']}"
            try:
                with requests.get(url, stream=True) as r:
                    with open(dest, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                print(f"✅ Model {m['file']} saved!")
            except Exception as e:
                print(f"❌ Error: {e}")

@app.on_event("startup")
async def startup_event():
    # সার্ভার চালু হওয়ার সাথে সাথে ব্যাকগ্রাউন্ডে মডেল ডাউনলোড হবে
    threading.Thread(target=install_models).start()

# ৫. চেক করার জন্য হোম পেজ
@app.get("/")
async def home():
    return {"status": "Running", "owner": "Shakil", "project": "AI MASTER PRO"}

# ৬. ভিডিও আপলোড এবং রিং এনিমেশন প্রসেসিং
@app.post("/api/process")
async def process_video(file: UploadFile = File(...)):
    try:
        # ফাইল সেভ করা
        file_ext = file.filename.split(".")[-1]
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{file_ext}")
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # মুভিপাই (MoviePy) দিয়ে ভিডিও চেক করা
        clip = VideoFileClip(input_path)
        output_filename = f"shakil_output_{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # এখানে ভবিষ্যতে আপনার রিং এনিমেশন লজিক ঢুকবে
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        return {"status": "success", "url": f"/outputs/{output_filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ৭. Render-এর জন্য ডাইনামিক পোর্ট সেটআপ (status 127 ফিক্স)
if __name__ == "__main__":
    import uvicorn
    # Render নিজে থেকে পোর্ট দেয়, তাই os.environ.get ব্যবহার করা হয়েছে
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
