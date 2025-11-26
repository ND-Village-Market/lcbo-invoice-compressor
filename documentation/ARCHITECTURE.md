# System Architecture & Data Flow

## 📋 Processing Pipeline

```
Input PDF (92 KB)
    ↓
[pdfplumber] Extract Text & Tables
    ↓
Parse Invoice Metadata (Order #, Date, Customer)
    ↓
Extract Product Data from All Pages
    ↓
Consolidate Data (Remove Duplicates)
    ↓
Calculate Totals (Subtotal + HST)
    ↓
[reportlab] Generate Condensed PDF
    ↓
Output PDF (5.2-8 KB)
```

## 🏗️ Class Architecture

```
LCBOInvoiceProcessor
├── __init__(pdf_path)
├── extract_invoice_info(pdf)
│   ├── Order number
│   ├── Order date
│   ├── Customer info
│   └── HST percentage
├── extract_products(pdf)
│   └── Parse all product rows
├── parse_product_line(line)
│   └── Extract individual product data
├── calculate_totals()
│   └── Compute final amounts
├── process()
│   └── Main extraction orchestration
└── generate_condensed_pdf(output_path)
    └── Create formatted output
```

## 📊 Data Extraction Flow

```
Raw PDF Text
    ↓
Regex Pattern Matching
    ├── ORDER # (\d+)
    ├── ORDER DATE (\d{1,2}/\d{1,2}/\d{4})
    ├── Customer #: (\d+)
    └── HST (\d+)%
    ↓
Product Line Parsing
    ├── Product ID
    ├── Size (mL)
    ├── Description
    ├── Quantities
    └── Prices
    ↓
Data Aggregation
    ├── All pages consolidated
    ├── Duplicates removed
    └── Totals calculated
    ↓
Output Data Structure
```

## 🎯 Column Transformation

| Original Columns | Condensed Output | Reason |
|---|---|---|
| PRODUCT # | ✓ Product | Essential for identification |
| SIZE (mL) | ✓ Size | Important specification |
| DESCRIPTION | ✓ Product (truncated) | Key info, space optimized |
| DEP | ✗ Removed | Not useful for review |
| ORDERED | ✓ Qty | Important quantity |
| SHIPPED | ✗ Removed | Usually matches ordered |
| RETAIL PRICE | ✗ Removed | Discount price more relevant |
| DISCOUNT PRICE | ✓ Price | What customer actually pays |
| EXTENDED PRICE | ✓ Total | Line item total |

## 💾 File Size Breakdown

```
Original PDF (92 KB)
├── Page 1: Headers, Tables, Footers
├── Page 2: Headers, Tables, Footers (repeated)
├── Page 3: Headers, Tables, Footers (repeated)
└── Page 4: Headers, Tables, Footers (repeated)

Condensed PDF (5.2-8 KB)
├── Header Section (Order info)
├── Single Consolidated Table
├── Summary/Totals
└── Footer
```

## 🔄 Batch Processing Workflow

```
batch_process.py
    ↓
Find all PDF files in directory
    ↓
For each PDF:
    ├── Create LCBOInvoiceProcessor
    ├── Extract data
    ├── Process to condensed PDF
    └── Log result
    ↓
Generate Summary Report
    ├── Total files
    ├── Success count
    ├── Error count
    └── Combined totals
    ↓
Output Console Report
```

## 📝 Data Structure

### Invoice Info Object
```python
{
    'order_number': '60581686',
    'order_date': '11/19/2025',
    'customer_name': 'NEW DUNDEE VILLAGE MARKET',
    'customer_number': '933201',
    'hst_percent': '13'
}
```

### Product Object
```python
{
    'product_number': '110056',
    'size_ml': '750',
    'description': 'Absolut Vodka',
    'ordered': 12,
    'shipped': 12,
    'retail_price': 29.35,
    'discount_price': 24.98,
    'extended_price': 299.76
}
```

### Totals Object
```python
{
    'subtotal': 8462.18,
    'hst': 1100.08,
    'total': 9562.26,
    'item_count': 41
}
```

## 🛠️ Technology Stack

```
Input Layer
└── pdfplumber: PDF text extraction

Processing Layer
├── re (regex): Pattern matching
├── pathlib: File handling
└── LCBOInvoiceProcessor: Data extraction

Output Layer
└── reportlab: PDF generation
    ├── SimpleDocTemplate
    ├── Table/TableStyle
    ├── Paragraph/ParagraphStyle
    └── Canvas elements
```

## 📈 Performance Metrics

- **Extraction Time**: ~1-2 seconds per PDF
- **PDF Generation Time**: ~2-3 seconds
- **Memory Usage**: ~50-100 MB per file
- **File Size Reduction**: 94%
- **Page Reduction**: 75-80%

## 🔐 Data Isolation

```
Virtual Environment (venv/)
├── bin/python3
├── bin/pip
└── lib/python3.x/
    ├── pdfplumber/
    ├── reportlab/
    ├── PyPDF2/
    └── pillow/

System Python
└── Unchanged
```

## 📚 API Reference Quick View

### Main Processing
```python
processor = LCBOInvoiceProcessor(pdf_path)
info, products = processor.process()
processor.generate_condensed_pdf(output_path)
```

### Batch Processing
```python
batch_process_pdfs(directory, pattern="*.pdf")
```

### Configuration
Edit in `pdf_processor.py`:
- `extract_invoice_info()` - Extraction logic
- `parse_product_line()` - Product parsing
- `generate_condensed_pdf()` - Output formatting

## 🧪 Testing Checklist

- [x] Virtual environment setup
- [x] Dependencies installation
- [x] PDF extraction accuracy
- [x] Data parsing correctness
- [x] Totals calculation verification
- [x] PDF generation success
- [x] File size reduction confirmation
- [x] Batch processing functionality
- [x] Error handling
- [x] Documentation completeness

---

**Architecture Version:** 1.0  
**Last Updated:** November 25, 2025
