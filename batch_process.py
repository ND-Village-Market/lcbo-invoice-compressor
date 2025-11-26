#!/usr/bin/env python3
"""
Batch PDF Invoice Processor - Process multiple PDF invoices at once
"""

import os
import glob
from pathlib import Path
from pdf_processor import LCBOInvoiceProcessor


def batch_process_pdfs(directory=".", pattern="*.pdf", skip_condensed=True):
    """Process all PDFs in a directory"""
    
    # Find all PDF files
    pdf_files = glob.glob(os.path.join(directory, pattern))
    
    # Skip already condensed files if requested
    if skip_condensed:
        pdf_files = [f for f in pdf_files if '_condensed' not in f]
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    print("=" * 70)
    
    results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"\n[{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_file)}")
            
            processor = LCBOInvoiceProcessor(pdf_file)
            invoice_info, products = processor.process()
            totals = processor.calculate_totals()
            
            # Generate condensed PDF
            output_file = pdf_file.replace('.pdf', '_condensed.pdf')
            processor.generate_condensed_pdf(output_file)
            
            result = {
                'input_file': os.path.basename(pdf_file),
                'output_file': os.path.basename(output_file),
                'order_number': invoice_info.get('order_number'),
                'order_date': invoice_info.get('order_date'),
                'customer': invoice_info.get('customer_name'),
                'items': len(products),
                'status': 'SUCCESS'
            }
            
            print(f"  ✓ Order #{result['order_number']} | {result['items']} items")
            
        except Exception as e:
            result = {
                'input_file': os.path.basename(pdf_file),
                'output_file': 'N/A',
                'status': 'ERROR',
                'error': str(e)
            }
            print(f"  ✗ Error: {str(e)}")
        
        results.append(result)
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"Total files processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print(f"\nTotal items processed: {sum(r.get('items', 0) for r in results if r['status'] == 'SUCCESS')}")


if __name__ == "__main__":
    import sys
    
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    batch_process_pdfs(directory)
