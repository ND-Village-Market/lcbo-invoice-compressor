# Testing Guide

## Prerequisites
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000
- Sample LCBO PDF files in the `invoices/` directory

## Frontend Testing

### 1. UI Components
- [ ] FileUpload component renders correctly
- [ ] Drag and drop zone is interactive
- [ ] File selection works via file picker
- [ ] File list displays selected files
- [ ] File removal buttons work
- [ ] Disabled state during processing works

### 2. File Upload
- [ ] Can select single PDF file
- [ ] Can select multiple PDF files
- [ ] Invalid file types are rejected
- [ ] File sizes are displayed correctly

### 3. Processing Results
- [ ] Results display after processing
- [ ] Success/error states show correctly
- [ ] Order number displays for successful files
- [ ] Customer name displays for successful files
- [ ] Item count displays correctly
- [ ] Error messages show for failed files

### 4. Download
- [ ] Download button appears for successful files
- [ ] Clicking download starts file download
- [ ] Downloaded file has correct name
- [ ] Downloaded file is readable PDF

### 5. Session Management
- [ ] "Process More Files" button appears after results
- [ ] Clicking it resets UI for new upload
- [ ] Multiple sessions can be created

## Backend Testing

### 1. Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### 2. File Upload
```bash
curl -X POST -F "files=@invoices/sample.pdf" http://localhost:8000/upload
# Expected: 200 with session_id and results
```

### 3. Download
```bash
# Using session_id from previous response
curl http://localhost:8000/download/{session_id}/{filename} \
  -o downloaded_file.pdf
```

### 4. List Files
```bash
curl http://localhost:8000/list/{session_id}
# Expected: {"session_id":"...", "files":["..."]}
```

### 5. Cleanup
```bash
curl -X DELETE http://localhost:8000/cleanup/{session_id}
# Expected: {"status":"cleaned", "session_id":"..."}
```

## API Documentation
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

## End-to-End Testing Checklist

### Scenario 1: Single File Processing
- [ ] Navigate to http://localhost:3000
- [ ] Select one PDF file from `invoices/`
- [ ] Click "Process Files"
- [ ] Wait for processing to complete
- [ ] Verify results display correctly
- [ ] Download the processed PDF
- [ ] Open downloaded file and verify content
- [ ] Verify page numbers are present
- [ ] Verify columns are correct (Product #, Size, Description, DEP, Ordered, Shipped, Received)
- [ ] Verify Product # is right-aligned
- [ ] Verify Size column is center-aligned
- [ ] Verify alternating row colors
- [ ] Verify bold rows for Ordered ≠ Shipped

### Scenario 2: Multiple File Processing
- [ ] Navigate to http://localhost:3000
- [ ] Select 2+ PDF files from `invoices/`
- [ ] Click "Process Files"
- [ ] Wait for all files to process
- [ ] Verify all results display
- [ ] Download each processed PDF
- [ ] Verify all files download correctly

### Scenario 3: Error Handling
- [ ] Try uploading non-PDF file
- [ ] Verify error message displays
- [ ] Try uploading corrupted PDF
- [ ] Verify error message displays
- [ ] Click "Process More Files"
- [ ] Verify UI resets correctly

### Scenario 4: File Management
- [ ] Upload files
- [ ] Check `/list/{session_id}` endpoint
- [ ] Verify all processed files listed
- [ ] Download files
- [ ] Call `/cleanup/{session_id}`
- [ ] Verify files are removed
- [ ] Verify files no longer available for download

## Performance Testing

### File Processing Speed
- Time single file processing: Target < 10 seconds
- Time multiple file processing: Target < 5 seconds each

### File Size Reduction
- Original file size: typically 90-100 KB
- Processed file size: target 5-10 KB
- Expected reduction: 90%+

## Browser Compatibility Testing

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Stress Testing

- [ ] Upload 5+ files simultaneously
- [ ] Upload very large PDFs (20+ MB)
- [ ] Rapid successive uploads
- [ ] System stability under load

## Cleanup

### After Testing
1. Stop frontend: `Ctrl+C` in frontend terminal
2. Stop backend: `Ctrl+C` in backend terminal
3. Clean temporary files: `rm -rf /tmp/lcbo_invoices/`
4. Check logs for errors

## Known Limitations

1. PDF extraction assumes LCBO invoice format
2. Multi-line descriptions may have edge cases
3. Large PDFs (>50 MB) may be slow
4. Temporary files kept for 24 hours before auto-cleanup

## Testing Report Template

```
Test Date: [DATE]
Tester: [NAME]
Environment: [OS, Python Version, Node Version]

Frontend Tests: [PASS/FAIL]
Backend Tests: [PASS/FAIL]
E2E Tests: [PASS/FAIL]
Performance: [PASS/FAIL]

Issues Found:
- [Issue 1]
- [Issue 2]

Notes:
- [Any additional notes]
```

## Continuous Testing

Run automated tests (when implemented):
```bash
cd frontend
npm test

cd ../backend
pytest
```
