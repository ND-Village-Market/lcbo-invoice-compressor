import os
import shutil
import tempfile
from pathlib import Path
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from pdf_processor import LCBOInvoiceProcessor

app = FastAPI(title="LCBO Invoice Processor", version="1.0.0")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temporary directory for processing
UPLOAD_DIR = Path(tempfile.gettempdir()) / "lcbo_invoices"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    """
    Upload one or more PDF files for processing
    Returns session ID and processing status
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    uploaded_files = []
    processing_results = []
    
    try:
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Save uploaded file
            file_path = session_dir / file.filename
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append(file.filename)
            
            try:
                # Process the PDF
                processor = LCBOInvoiceProcessor(str(file_path))
                invoice_info, products = processor.process()
                
                # Generate condensed PDF
                output_filename = file.filename.replace('.pdf', '_condensed.pdf')
                output_path = session_dir / output_filename
                processor.generate_condensed_pdf(str(output_path))
                
                processing_results.append({
                    "original_file": file.filename,
                    "output_file": output_filename,
                    "order_number": invoice_info.get('order_number'),
                    "customer_name": invoice_info.get('customer_name'),
                    "item_count": len(products),
                    "status": "success"
                })
            except Exception as e:
                processing_results.append({
                    "original_file": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "session_id": session_id,
            "files_uploaded": len(uploaded_files),
            "processing_results": processing_results
        }
    
    except Exception as e:
        # Clean up on error
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{session_id}/{filename}")
async def download_pdf(session_id: str, filename: str):
    """
    Download a processed PDF file
    """
    file_path = UPLOAD_DIR / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )


@app.get("/list/{session_id}")
async def list_files(session_id: str):
    """
    List all processed files in a session
    """
    session_dir = UPLOAD_DIR / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    files = [
        f.name for f in session_dir.iterdir() 
        if f.is_file() and f.name.endswith('_condensed.pdf')
    ]
    
    return {"session_id": session_id, "files": files}


@app.delete("/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Clean up session files
    """
    session_dir = UPLOAD_DIR / session_id
    
    if session_dir.exists():
        shutil.rmtree(session_dir)
    
    return {"status": "cleaned", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
