# LCBO Document Tools

Web app for processing LCBO PDFs.

It currently supports:
- Invoice condenser: upload invoice PDFs and download condensed PDF versions
- Supplier CSV extractor: upload item-list PDFs and generate CSV with `sku,qty`

## Tech Stack

- Backend: FastAPI + pdfplumber + reportlab
- Frontend: React (Create React App)

## Local Development Setup

### Prerequisites

- Python 3.10+ (3.11+ recommended)
- Node.js 18+ and npm

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd lcbo-invoice-compressor
```

### 2. Set up backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up frontend

Open a second terminal:

```bash
cd frontend
npm install
```

## Run Locally (Backend + Frontend)

### Terminal A: start backend API

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Backend endpoints:
- API base: http://localhost:8001
- Swagger docs: http://localhost:8001/docs
- Health check: http://localhost:8001/health

### Terminal B: start frontend

```bash
cd frontend
npm start
```

Frontend app:
- http://localhost:3000

Notes:
- In development, frontend defaults to `http://localhost:8001` for API calls.
- If you want to point to a different API URL, set `REACT_APP_API_URL` before `npm start`.

## Optional One-Command Scripts

From project root:

```bash
./scripts/setup_web.sh
./scripts/start.sh
```

These scripts create backend venv (if missing), install dependencies, and start both servers.

## Features

- Condense multi-page invoices into cleaner PDFs
- Remove repetitive invoice noise while preserving key order/item details
- Extract supplier numbers from item-list PDFs
- Normalize supplier values to digits only with leading zeros removed
- Export spreadsheet-friendly CSV with columns `sku,qty` (qty always `1`)

## Project Structure

```text
backend/
   main.py
   pdf_processor.py
   supplier_csv_processor.py
   requirements.txt
frontend/
   package.json
   src/
scripts/
   setup_web.sh
   start.sh
```

## Troubleshooting

### Backend imports unresolved in editor

Your editor may be using a different Python interpreter.
Select `backend/venv/bin/python` as the active Python interpreter.

### CORS / API connection issues

- Confirm backend is running on port `8001`
- Confirm frontend is running on port `3000`
- Confirm `REACT_APP_API_URL` (if set) points to the correct backend URL

### npm start fails

Delete and reinstall dependencies:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

## License

Free to use and modify.
