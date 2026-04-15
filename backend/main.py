import shutil
import tempfile
from pathlib import Path
import uuid
import csv
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from pdf_processor import LCBOInvoiceProcessor
from supplier_csv_processor import SupplierCSVExtractor
from wholesale_cost_processor import WholesaleCostCalculator

app = FastAPI(title="LCBO Invoice Processor", version="1.0.0")

# Add CORS middleware to allow requests from local frontend origins.
# Use CORS_ORIGINS to override defaults when needed.
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,https://lcboic.netlify.app",
)
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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


@app.post("/extract-supplier-csv")
async def extract_supplier_csv(file: UploadFile = File(...)):
    """
    Upload a PDF item list and generate supplier CSV.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")

    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    try:
        source_pdf_path = session_dir / file.filename
        with open(source_pdf_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        extractor = SupplierCSVExtractor(str(source_pdf_path))
        suppliers = extractor.extract_suppliers()

        base_name = file.filename.rsplit('.', 1)[0]
        csv_files = extractor.generate_chunked_csvs(str(session_dir), base_name)
        row_count = len(suppliers)

        return {
            "session_id": session_id,
            "original_file": file.filename,
            "csv_file": csv_files[0],
            "csv_files": csv_files,
            "csv_file_count": len(csv_files),
            "supplier_count": row_count,
            "status": "success" if suppliers else "empty"
        }
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calculate-item-cost-csv")
async def calculate_item_cost_csv(session_id: str, files: list[UploadFile] = File(...)):
    """
    Step 2: Upload a Quick Order PDF and generate item-cost CSV.
    Uses item numbers extracted in step 1 from the same session.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    for file in files:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="One or more files are missing")
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")

    session_dir = UPLOAD_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    supplier_csv_candidates = sorted(session_dir.glob('*_supplier_skus*.csv'))
    if not supplier_csv_candidates:
        raise HTTPException(status_code=400, detail="Step 1 CSV not found for this session")

    allowed_items = set()
    for csv_path in supplier_csv_candidates:
        with csv_path.open('r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                sku = (row.get('sku') or '').strip()
                if sku:
                    allowed_items.add(sku)

    if not allowed_items:
        raise HTTPException(status_code=400, detail="Step 1 CSV is empty")

    processing_results = []

    for file in files:
        try:
            quick_order_path = session_dir / file.filename
            with open(quick_order_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            calculator = WholesaleCostCalculator(str(quick_order_path))
            rows = calculator.calculate_cost_rows(allowed_items)

            output_filename = file.filename.rsplit('.', 1)[0] + '_item_costs.csv'
            output_path = session_dir / output_filename
            row_count = WholesaleCostCalculator.write_item_cost_csv(str(output_path), rows)

            processing_results.append({
                "original_file": file.filename,
                "csv_file": output_filename,
                "item_count": row_count,
                "status": "success" if row_count > 0 else "empty"
            })
        except Exception as e:
            processing_results.append({
                "original_file": file.filename,
                "status": "error",
                "error": str(e)
            })

    return {
        "session_id": session_id,
        "files_uploaded": len(files),
        "processing_results": processing_results,
    }


@app.get("/download/{session_id}/{filename}")
async def download_pdf(session_id: str, filename: str):
    """
    Download a processed PDF file
    """
    file_path = UPLOAD_DIR / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "application/pdf"
    if filename.lower().endswith('.csv'):
        media_type = "text/csv"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
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
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
