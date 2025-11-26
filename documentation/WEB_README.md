# LCBO Invoice Processor - Web Application

A web-based application for processing LCBO (Liquor Control Board of Ontario) invoice PDFs, removing unnecessary information and creating condensed, readable versions.

## Features

- 📤 **Upload Multiple PDFs**: Drag and drop or select one or more PDF files
- ⚡ **Batch Processing**: Process multiple invoices simultaneously
- 📊 **Smart Extraction**: Automatically extracts order info, product details, and quantities
- 🎨 **Formatted Output**: Creates professional, easy-to-read condensed PDFs
- 💾 **Download Results**: Download processed PDFs individually
- 🌐 **Web-Based**: No installation required, access from any browser

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  React Frontend (Port 3000)                              │
│  - File Upload Component                                 │
│  - Drag & Drop Interface                                 │
│  - Results Display & Download                            │
│                                                           │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────┐
│                                                           │
│  FastAPI Backend (Port 8000)                             │
│  - /upload - Process PDF files                           │
│  - /download - Download processed PDFs                   │
│  - /list - List processed files                          │
│  - /cleanup - Clean up session files                     │
│                                                           │
│  PDF Processor Engine                                    │
│  - Invoice Info Extraction (Order #, Date, Customer)    │
│  - Product Data Extraction & Parsing                     │
│  - PDF Generation with ReportLab                         │
│  - Page Numbering & Formatting                           │
│                                                           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  Temporary Storage    │
           │  (Processing Files)   │
           └───────────────────────┘
```

## Project Structure

```
lcbo_compress/
├── backend/
│   ├── main.py                 # FastAPI app with endpoints
│   ├── pdf_processor.py        # PDF processing logic
│   ├── requirements.txt        # Python dependencies
│   └── __init__.py
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.js   # Upload component
│   │   │   ├── FileUpload.css
│   │   │   ├── ProcessingResults.js  # Results component
│   │   │   └── ProcessingResults.css
│   │   ├── App.js              # Main app component
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── .gitignore
├── start.sh                    # Startup script
├── README.md                   # This file
└── ...old files...
```

## Installation & Setup

### Prerequisites
- Python 3.7+
- Node.js 14+
- npm or yarn

### Quick Start

1. **Make the startup script executable**:
   ```bash
   chmod +x start.sh
   ```

2. **Run the application**:
   ```bash
   ./start.sh
   ```

   The script will:
   - Create a Python virtual environment (if needed)
   - Install Python dependencies
   - Install npm packages (if needed)
   - Start the backend server (Port 8000)
   - Start the frontend server (Port 3000)

3. **Open in browser**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs (interactive API docs)

### Manual Setup (Alternative)

**Backend Setup**:
```bash
# Create virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup** (in another terminal):
```bash
cd frontend
npm install
npm start
```

## API Endpoints

### POST /upload
Upload and process PDF files.

**Request**:
- Content-Type: multipart/form-data
- Parameter: `files` (multiple PDF files)

**Response**:
```json
{
  "session_id": "uuid-string",
  "files_uploaded": 2,
  "processing_results": [
    {
      "original_file": "invoice1.pdf",
      "output_file": "invoice1_condensed.pdf",
      "order_number": "60572047",
      "customer_name": "ABC Liquor Store",
      "item_count": 54,
      "status": "success"
    }
  ]
}
```

### GET /download/{session_id}/{filename}
Download a processed PDF file.

### GET /list/{session_id}
List all processed files in a session.

**Response**:
```json
{
  "session_id": "uuid-string",
  "files": ["invoice1_condensed.pdf", "invoice2_condensed.pdf"]
}
```

### DELETE /cleanup/{session_id}
Clean up session files.

### GET /health
Health check endpoint.

## Features & Capabilities

### PDF Processing
- Extracts order number, date, customer name
- Extracts product information:
  - Product number
  - Size (handles complex formats like "8 x 355")
  - Description (multi-line support)
  - Deposit amount (DEP)
  - Ordered and shipped quantities
- Removes unnecessary columns (prices, discounts, extended prices)
- Sorts products alphabetically by description
- Highlights rows where ordered ≠ shipped (bold text)

### Output Formatting
- Condensed PDF with relevant information only
- 94% file size reduction (typically 92KB → 5-8KB)
- Professional table formatting
- Alternating row colors for readability
- Page numbers in format "X / Y"
- Center-aligned Size column
- Right-aligned Product # column
- Empty "Received" column for manual entry
- **Print-safe 0.5" margins on all sides** (no cutoff when printing)

## Technology Stack

### Frontend
- React 18
- CSS3 with flexbox/grid
- Fetch API for HTTP requests

### Backend
- FastAPI (Python web framework)
- Uvicorn (ASGI server)
- pdfplumber (PDF text extraction)
- reportlab (PDF generation)
- PyPDF2 (PDF manipulation)
- python-multipart (form data handling)

### Infrastructure
- Temporary file storage for processing
- Session-based file management
- CORS enabled for cross-origin requests

## Usage Guide

1. **Upload Files**:
   - Click the drop zone or use the file browser
   - Select one or more PDF files
   - Files are validated to be PDFs
   - File list shows selected files with sizes

2. **Process**:
   - Click "Process Files" button
   - Backend processes each file
   - Progress shown in UI

3. **Download Results**:
   - View results summary
   - Download individual processed PDFs
   - Order information displayed

4. **Process More**:
   - Click "Process More Files" to upload new batch
   - Previous session is retained for 24 hours (auto-cleanup available)

## Error Handling

- Invalid file types are rejected
- PDF extraction errors are caught and reported
- Failed files show error messages
- Session cleanup on errors prevents disk space issues
- API returns appropriate HTTP status codes

## Performance

- **File Processing**: ~5-10 seconds per PDF
- **File Size Reduction**: 94% average
- **Scalability**: Can process multiple files concurrently
- **Storage**: Temporary files auto-cleanup (24 hours)

## Security Considerations

- CORS enabled for all origins (production: restrict as needed)
- File type validation on upload
- Temporary files stored in system temp directory
- No files permanently stored on server
- Session-based access (no directory traversal)

## Troubleshooting

### Backend won't start
```bash
# Check Python installation
python3 --version

# Reinstall dependencies
source backend/venv/bin/activate
pip install --upgrade -r backend/requirements.txt
```

### Frontend won't start
```bash
# Check Node.js installation
node --version
npm --version

# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### CORS errors
Ensure backend is running on http://localhost:8000 and frontend on http://localhost:3000

### Port already in use
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

## Future Enhancements

- User authentication & file history
- Support for additional invoice formats
- CSV export option
- Advanced filtering & search
- Customizable output templates
- Direct email delivery of processed PDFs
- Batch scheduling & automation

## License

This project is for internal use by LCBO.

## Support

For issues or feature requests, contact the development team.
