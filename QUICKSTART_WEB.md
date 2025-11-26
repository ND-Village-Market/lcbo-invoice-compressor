# LCBO Invoice Processor - Quick Reference

## Quick Start (One Command)

```bash
chmod +x setup_web.sh start.sh && ./setup_web.sh && ./start.sh
```

Then open: http://localhost:3000

## Directory Structure

```
backend/          → FastAPI REST API (port 8000)
frontend/         → React UI (port 3000)
invoices/         → Sample PDF files
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | REST endpoints |
| `backend/pdf_processor.py` | PDF processing logic |
| `frontend/src/App.js` | Main React component |
| `frontend/src/components/FileUpload.js` | Upload interface |
| `frontend/src/components/ProcessingResults.js` | Results display |

## API Endpoints

```
POST   /upload                          → Process PDFs
GET    /download/{session_id}/{file}    → Download PDF
GET    /list/{session_id}               → List files
DELETE /cleanup/{session_id}            → Delete session
GET    /health                          → Health check
GET    /docs                            → API documentation
```

## Manual Start (Separate Terminals)

**Terminal 1**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2**:
```bash
cd frontend
npm install
npm start
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -i :8000 \| grep LISTEN \| awk '{print $2}' \| xargs kill -9` |
| Port 3000 in use | `lsof -i :3000 \| grep LISTEN \| awk '{print $2}' \| xargs kill -9` |
| Module errors | Reinstall: `pip install -r backend/requirements.txt` or `npm install` |
| CORS errors | Ensure backend on 8000, frontend on 3000 |

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |

## Testing

```bash
# Test backend
curl http://localhost:8000/health

# Test upload
curl -X POST -F "files=@invoices/sample.pdf" http://localhost:8000/upload

# View API docs
open http://localhost:8000/docs
```

## Environment Variables

**Frontend** (.env):
```
REACT_APP_API_URL=http://localhost:8000
```

## File Formats

- **Input**: PDF (LCBO invoices)
- **Output**: PDF (condensed, formatted)
- **Reduction**: ~94% (90KB → 5KB typical)

## Key Features

- ✓ Drag & drop upload
- ✓ Batch processing (multiple files)
- ✓ Real-time progress
- ✓ Individual downloads
- ✓ Session management
- ✓ Error handling
- ✓ Mobile responsive

## Documentation

- **Full README**: `WEB_README.md`
- **Testing Guide**: `TESTING.md`
- **Migration Info**: `MIGRATION.md`
- **Architecture**: See WEB_README.md

## Stopping the App

```bash
# Stop frontend: Ctrl+C
# Stop backend: Ctrl+C
# Clean temp files: rm -rf /tmp/lcbo_invoices/
```

## Dependencies

**Backend**:
- FastAPI, Uvicorn
- pdfplumber, reportlab, PyPDF2

**Frontend**:
- React, React-DOM

## Contact & Support

For issues or questions, refer to the detailed documentation:
- Backend structure: `backend/main.py`
- Frontend structure: `frontend/src/App.js`
- API documentation: http://localhost:8000/docs

---

**Pro Tip**: The setup script automates everything. Just run `./setup_web.sh` once!
