#!/bin/bash
# Setup script for PDF Processor

echo "Setting up LCBO Invoice PDF Processor..."
echo "========================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install packages
echo "Installing dependencies..."
source venv/bin/activate
pip install -q pypdf2 reportlab pdfplumber pillow

echo "✓ Dependencies installed"
echo ""
echo "Setup complete!"
echo ""
echo "To use the processor:"
echo "  1. Activate: source venv/bin/activate"
echo "  2. Run:      python3 pdf_processor.py"
echo ""
echo "For batch processing:"
echo "  python3 batch_process.py [directory]"
