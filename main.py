from fastapi import FastAPI
from app.routers import new_pdf_to_jpg

app = FastAPI(
    title="PDF Tools API",
    version="1.0"
)

app.include_router(new_pdf_to_jpg.router)
