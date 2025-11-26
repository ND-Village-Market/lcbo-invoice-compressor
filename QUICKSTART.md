# Quick Start Guide

## One-Time Setup

```bash
cd /Users/anujpatel/lcbo_compress
bash setup.sh
```

## Process a Single PDF

```bash
cd /Users/anujpatel/lcbo_compress
source venv/bin/activate
python3 pdf_processor.py
```

**Output:** `Nov 19, 2025 invoice_condensed.pdf`

## Process Multiple PDFs

```bash
cd /Users/anujpatel/lcbo_compress
source venv/bin/activate
python3 batch_process.py
```

## What Changed

### Original PDF (92 KB, 4 pages)
- Headers repeated on every page
- Redundant customer info
- Full layout with spacing
- All columns included (deposit, etc.)

### Condensed PDF (5.2 KB, ~1-2 pages)
- Clean header section
- Single products table
- Optimized layout
- Only relevant columns
- Clear totals section

## Results

✓ 94% file size reduction
✓ Better readability
✓ More useful for sharing/printing
✓ Professional appearance
✓ All important data preserved

## Files Included

- `pdf_processor.py` - Single PDF processor
- `batch_process.py` - Batch processor for multiple PDFs
- `setup.sh` - Automated setup script
- `README.md` - Full documentation
- `QUICKSTART.md` - This file

## Troubleshooting

**Virtual environment not working?**
```bash
rm -rf venv
bash setup.sh
```

**Want to process PDFs in another folder?**
```bash
source venv/bin/activate
python3 batch_process.py /path/to/pdf/folder
```

**Need to customize the output?**
Edit the `generate_condensed_pdf()` method in `pdf_processor.py` to adjust colors, fonts, columns, etc.
