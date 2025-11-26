# Architecture & Data Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          React Frontend (Port 3000)                     │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │         FileUpload Component                    │   │    │
│  │  │  • Drag & Drop Zone                            │   │    │
│  │  │  • File Picker Button                          │   │    │
│  │  │  • File List Display                           │   │    │
│  │  │  • Progress Indicator                          │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                      │                                  │    │
│  │                      ▼                                  │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │      ProcessingResults Component                │   │    │
│  │  │  • Results Summary                             │   │    │
│  │  │  • Status Indicators (✓/✕)                     │   │    │
│  │  │  • Download Buttons                            │   │    │
│  │  │  • Error Messages                              │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            │ Fetch API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              REST API Endpoints                        │    │
│  │                                                          │    │
│  │  POST   /upload              - Process files           │    │
│  │  GET    /download/{id}/{fn}  - Download PDF           │    │
│  │  GET    /list/{id}           - List files             │    │
│  │  DELETE /cleanup/{id}        - Clean session          │    │
│  │  GET    /health              - Health check           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           LCBOInvoiceProcessor                         │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │ PDF Processing Pipeline                       │   │    │
│  │  │                                                │   │    │
│  │  │  1. Extract Invoice Info                      │   │    │
│  │  │     └─ Order #, Date, Customer               │   │    │
│  │  │                                                │   │    │
│  │  │  2. Extract Products (Multi-page)             │   │    │
│  │  │     ├─ Product #, Size, Description          │   │    │
│  │  │     ├─ Deposit, Ordered, Shipped             │   │    │
│  │  │     └─ Handle multi-line descriptions        │   │    │
│  │  │                                                │   │    │
│  │  │  3. Generate Condensed PDF                    │   │    │
│  │  │     ├─ Format with ReportLab                 │   │    │
│  │  │     ├─ Sort alphabetically                   │   │    │
│  │  │     ├─ Apply styling & colors                │   │    │
│  │  │     └─ Add page numbers via PyPDF2           │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌──────────────────────────┐
            │  Temporary Storage       │
            │  /tmp/lcbo_invoices/     │
            │                          │
            │  ├─ {session_id}/        │
            │  │  ├─ original.pdf      │
            │  │  └─ condensed.pdf     │
            │  │                       │
            │  └─ {session_id}/        │
            │     ├─ file1.pdf         │
            │     └─ file1_condensed   │
            │                          │
            │  (Auto-cleanup after 24h)│
            └──────────────────────────┘
```

## Data Flow Diagram

### 1. Upload Flow
```
User selects PDFs
        │
        ▼
Browser validates files (PDF type)
        │
        ▼
FormData created with files
        │
        ▼
POST /upload → Backend
        │
        ▼
Backend creates session (UUID)
        │
        ▼
For each file:
  ├─ Save to temp directory
  ├─ Process PDF (extract data)
  ├─ Generate condensed PDF
  └─ Record result (success/error)
        │
        ▼
Response: session_id + results array
        │
        ▼
Browser displays results
```

### 2. Download Flow
```
User clicks Download button
        │
        ▼
Frontend knows: session_id, filename
        │
        ▼
GET /download/{session_id}/{filename}
        │
        ▼
Backend retrieves file from temp storage
        │
        ▼
File sent as PDF response
        │
        ▼
Browser download triggered
```

## Session Management

```
Session Created
        │
        ├─ session_id (UUID)
        │
        ├─ session_dir (/tmp/lcbo_invoices/{session_id}/)
        │
        └─ lifecycle:
            ├─ Files uploaded and processed (0-5 minutes)
            ├─ User downloads results (5-30 minutes)
            ├─ Session remains for 24 hours
            └─ Auto-cleanup after 24 hours

Multiple Sessions
        │
        ├─ Session 1: user1 uploads 2 files
        ├─ Session 2: user2 uploads 1 file
        ├─ Session 3: user1 uploads 5 files
        │
        └─ Each session is independent
```

## PDF Processing Pipeline

```
Input PDF (LCBO Invoice)
        │
        ▼
1. Text Extraction (pdfplumber)
        │
        ├─ Page-by-page text parsing
        ├─ Table detection and extraction
        └─ Store as list of lines
        │
        ▼
2. Invoice Info Extraction (Regex)
        │
        ├─ Extract Order #
        ├─ Extract Order Date
        ├─ Extract Customer Name
        └─ Extract Customer #
        │
        ▼
3. Product Data Extraction
        │
        ├─ Identify product lines (start with number)
        ├─ Parse product number, size, description
        ├─ Extract DEP (deposit) value
        ├─ Extract Ordered and Shipped quantities
        └─ Handle multi-line descriptions
        │
        ▼
4. Data Cleaning
        │
        ├─ Remove duplicate products
        ├─ Standardize formats
        ├─ Resolve multi-line descriptions
        └─ Validate required fields
        │
        ▼
5. PDF Generation (ReportLab)
        │
        ├─ Create document structure
        ├─ Add title and invoice info table
        ├─ Sort products alphabetically
        ├─ Create products table with columns:
        │  └─ Product #, Size, Description, DEP, Ordered, Shipped, Received
        ├─ Apply styling:
        │  ├─ Blue header row
        │  ├─ Alternating white/gray rows
        │  ├─ Bold rows where Ordered ≠ Shipped
        │  └─ Right-align Product #, Center-align Size
        └─ Generate PDF
        │
        ▼
6. Post-processing (PyPDF2)
        │
        ├─ Add page numbers in format "X / Y"
        ├─ Overlay page numbers on existing PDF
        └─ Save final PDF
        │
        ▼
Output PDF (~94% size reduction)
        ├─ Original: ~92 KB
        ├─ Condensed: ~5-8 KB
        └─ Contains: Order info + formatted product table
```

## Component Hierarchy

```
App
├── FileUpload (or ProcessingResults)
│   ├── Drop Zone
│   ├── File Input
│   └── Selected Files List
│       └── File Items with Remove Buttons
│
├── ProcessingResults
│   ├── Results Summary
│   └── Results List
│       └── Result Items
│           ├── Status Indicator
│           ├── File Info
│           ├── Order Details
│           └── Download Button
│
└── Footer
```

## Request/Response Examples

### Upload Request
```
POST /upload HTTP/1.1
Content-Type: multipart/form-data

files: [binary PDF 1, binary PDF 2]
```

### Upload Response
```json
{
  "session_id": "a1b2c3d4-e5f6-g7h8-i9j0",
  "files_uploaded": 2,
  "processing_results": [
    {
      "original_file": "invoice1.pdf",
      "output_file": "invoice1_condensed.pdf",
      "order_number": "60572047",
      "customer_name": "ABC Liquor Store",
      "item_count": 54,
      "status": "success"
    },
    {
      "original_file": "invoice2.pdf",
      "output_file": "invoice2_condensed.pdf",
      "order_number": "60581686",
      "customer_name": "XYZ Beverages",
      "item_count": 41,
      "status": "success"
    }
  ]
}
```

### Download Request
```
GET /download/a1b2c3d4-e5f6-g7h8-i9j0/invoice1_condensed.pdf
```

### Download Response
```
[Binary PDF content sent to browser]
Content-Type: application/pdf
Content-Disposition: attachment; filename="invoice1_condensed.pdf"
```

## Error Handling Flow

```
Error Occurs
        │
        ├─ Validation Error (e.g., not a PDF)
        │   │
        │   └─ HTTP 400 + error message
        │
        ├─ Processing Error (e.g., invalid PDF)
        │   │
        │   └─ Return error in results array
        │   └─ Show error in UI
        │
        ├─ Server Error (e.g., disk full)
        │   │
        │   └─ HTTP 500 + error message
        │
        └─ File Not Found (e.g., download old session)
            │
            └─ HTTP 404 + error message
```

## Performance Characteristics

```
Single File Processing:
Input: 92 KB LCBO invoice PDF
  ├─ Extraction: ~2-3 seconds
  ├─ Processing: ~1-2 seconds
  ├─ PDF Generation: ~1-2 seconds
  └─ Total: ~5-10 seconds
Output: 5-8 KB condensed PDF
Reduction: 94%

Multiple Files (5 PDFs):
  ├─ Sequential processing
  ├─ ~30 seconds total
  └─ Output: 25-40 KB

API Response Times:
  ├─ Health check: <10ms
  ├─ List files: <50ms
  ├─ Download: <500ms
  └─ Cleanup: <100ms
```

---

This architecture ensures:
- ✓ Scalability (session-based isolation)
- ✓ Reliability (error handling at each step)
- ✓ Performance (efficient processing pipeline)
- ✓ User Experience (responsive UI)
- ✓ Maintainability (clean separation of concerns)
