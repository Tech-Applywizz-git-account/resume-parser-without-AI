import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from parser import ResumeParser, extract_text_from_file
import uvicorn

app = FastAPI(
    title="ApplyWizz Intelligence Engine",
    description="Production-grade rule-based resume parser with 90%+ accuracy.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def get_dashboard():
    """Serves the Recruitment Intelligence Terminal UI."""
    return FileResponse("index.html")

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    """
    Main Production Endpoint.
    Accepts: PDF, DOCX
    Returns: Structured JSON
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Use UUID to prevent file collisions in production
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save file to disk temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 1. Extraction Layer (Text + Metadata Links)
        text, links = extract_text_from_file(file_path)
        
        # 2. Intelligence Layer (Structural Analysis)
        parser = ResumeParser(text, links=links)
        result = parser.parse()
        
        # 3. Clean up immediately to keep server light
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return result
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Parsing Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)