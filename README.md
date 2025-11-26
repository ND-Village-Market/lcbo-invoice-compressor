# LCBO Invoice PDF Processor

A Python tool that processes LCBO (Ontario Liquor Commission Board) invoice PDFs to remove unnecessary information, reformat data, and create more concise, readable PDFs.

## Features

- **Consolidates multi-page invoices** into clean, condensed documents
- **Removes redundant information** (headers, footers, deposit columns)
- **Extracts key data**: Order #, Date, Customer, Items, Totals
- **Compact table layout** displaying only essential information
- **Significant file size reduction** (92KB → 5.2KB in test)
- **Batch processing** capability for multiple invoices
- **Professional formatting** with proper styling and alignment

## What Gets Removed

- Repetitive page headers and footers on each page
- Deposit percentage column (not useful for review)
- Redundant customer information across pages
- Excess whitespace and formatting

## What Gets Kept/Improved

- Product descriptions (first 40 characters)
- Order quantities
- Discount prices (more relevant than retail)
- Line item totals
- Summary totals with HST calculation
- Key invoice metadata (Order #, Date, Customer, etc.)

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pypdf2 reportlab pdfplumber pillow
```

## Usage

### Single PDF Processing

```bash
# Activate virtual environment
source venv/bin/activate

# Process a single PDF
python3 pdf_processor.py
```

This will:
- Look for `Nov 19, 2025 invoice.pdf` in the current directory
- Extract and analyze all invoice data
- Create `Nov 19, 2025 invoice_condensed.pdf`
- Display summary information

### Batch Processing

```bash
# Process all PDFs in current directory
python3 batch_process.py

# Process all PDFs in a specific directory
python3 batch_process.py /path/to/pdf/directory
```

This will:
- Find all PDF files in the directory
- Process each one sequentially
- Create condensed versions with `_condensed.pdf` suffix
- Display a summary report

## Output

The condensed PDF includes:

1. **Header Section**
   - Order number and date
   - Customer name and number

2. **Products Table**
   - Product name (truncated)
   - Size in mL
   - Quantity ordered
   - Discount price per unit
   - Extended total

3. **Summary Section**
   - Subtotal
   - HST (13% for Ontario)
   - Final total

## File Size Comparison

- Original invoice: 92 KB (4 pages with repetitive formatting)
- Condensed invoice: 5.2 KB (typically 1-2 pages)
- **Reduction: ~94%**

## Customization

Edit `pdf_processor.py` to customize:

- Column widths in the products table
- Font sizes and colors
- Included/excluded columns
- Rounding and formatting
- Page size and margins

## Requirements

- Python 3.7+
- pdfplumber (PDF text extraction)
- reportlab (PDF generation)
- pypdf2 (PDF manipulation)
- pillow (Image processing)

## License

Free to use and modify for your needs.

## Troubleshooting

**"External managed environment" error during pip install:**
- Use the provided virtual environment setup
- Or use: `pip install --break-system-packages` (not recommended)

**Generated PDF is blank:**
- Check that the input PDF has extractable text
- Verify the PDF format is compatible
- Check file permissions

**Incorrect data extraction:**
- Verify the PDF format matches LCBO standard invoices
- Modify regex patterns in `extract_invoice_info()` if needed
- Check the `parse_product_line()` method for custom formats

## Future Enhancements

- Support for other PDF invoice formats
- Custom column selection
- Multi-invoice comparison reports
- CSV export option
- Web interface
- Automated scheduling
