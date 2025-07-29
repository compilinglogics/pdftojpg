from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
import fitz  # PyMuPDF

router = APIRouter()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_KEY = "saif-00-22"

def verify_api_key(key: str):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

def convert_pdf_to_images(pdf_path: str, file_id: str):
    try:
        doc = fitz.open(pdf_path)
        image_links = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=200)
            img_filename = f"{file_id}_page_{i + 1}.jpg"
            img_path = os.path.join(OUTPUT_DIR, img_filename)
            pix.save(img_path)
            image_links.append(f"/download/{img_filename}")
        return image_links
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.post("/convert", tags=["PDF to JPG"])
async def convert_pdf(api_key: str = Form(...), file: UploadFile = File(...)):
    verify_api_key(api_key)
    file_id = str(uuid.uuid4())
    input_pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(input_pdf_path, "wb") as f:
        f.write(await file.read())

    download_links = convert_pdf_to_images(input_pdf_path, file_id)
    return JSONResponse({"file_id": file_id, "download_links": download_links})

@router.get("/download/{filename}", tags=["PDF to JPG"])
def download_image(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    return FileResponse(file_path, media_type="image/jpeg", filename=filename)
