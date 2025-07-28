from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
import requests
from pdf2image import convert_from_path

app = FastAPI(
    title="Dynamic PDF to JPG Converter",
    description="Convert PDF files to JPG using upload or URL",
    version="2.1"
)

API_KEY = "saif-00-22"

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------- Utility Functions --------------------

def verify_api_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

def save_uploaded_file(file: UploadFile, save_path: str):
    try:
        with open(save_path, "wb") as f:
            contents = file.file.read()
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def save_pdf_from_url(url: str, save_path: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf",
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch PDF: {str(e)}")

def convert_pdf_to_images(pdf_path: str, file_id: str):
    try:
        images = convert_from_path(pdf_path, dpi=200)
        image_links = []
        for i, img in enumerate(images):
            img_filename = f"{file_id}_page_{i + 1}.jpg"
            img_path = os.path.join(OUTPUT_DIR, img_filename)
            img.save(img_path, "JPEG")
            image_links.append(f"/download/{img_filename}")
        return image_links
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

# -------------------- Routes --------------------

@app.post("/convert/file", tags=["PDF to JPG"], summary="Convert PDF via File Upload")
async def convert_from_file(
    api_key: str = Form(...),
    file: UploadFile = File(...)
):
    verify_api_key(api_key)
    file_id = str(uuid.uuid4())
    input_pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    save_uploaded_file(file, input_pdf_path)
    download_links = convert_pdf_to_images(input_pdf_path, file_id)
    return JSONResponse({"file_id": file_id, "download_links": download_links})

@app.post("/convert/url", tags=["PDF to JPG"], summary="Convert PDF via URL")
async def convert_from_url(
    api_key: str = Form(...),
    url: str = Form(...)
):
    verify_api_key(api_key)
    file_id = str(uuid.uuid4())
    input_pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    save_pdf_from_url(url, input_pdf_path)
    download_links = convert_pdf_to_images(input_pdf_path, file_id)
    return JSONResponse({"file_id": file_id, "download_links": download_links})

@app.get("/download/{filename}", tags=["PDF to JPG"], summary="Download converted image")
async def download_converted_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(file_path, media_type="image/jpeg", filename=filename)
