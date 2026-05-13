import os
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.main import start_project

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
DATA_DIR = "data"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


@app.get("/")
def root():
    return {"message": "backend is running"}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    model_name: str = Form("qwen-vl-plus")
):
    ext = os.path.splitext(file.filename)[1] or ".png"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = start_project(image_path=file_path, use_llm=True, model_name=model_name)

    image_stem = os.path.splitext(unique_name)[0]
    detect_image_name = f"{image_stem}_detect.jpg"
    detect_image_path = os.path.join(DATA_DIR, detect_image_name)

    detect_image_url = ""
    if os.path.exists(detect_image_path):
        detect_image_url = f"http://127.0.0.1:8000/data/{detect_image_name}"

    return {
        "message": "识别完成",
        "filename": file.filename,
        "code": result.get("vue_code", ""),
        "preview_html": result.get("preview_html", ""),
        "layout_tree": result.get("layout_tree", []),
        "detections": result.get("detections", []),
        "detect_image_url": detect_image_url,
        "llm_used": result.get("llm_used", False),
        "llm_error": result.get("llm_error", ""),
        "similarity": result.get("similarity", {}),
        "model_name": model_name,
    }