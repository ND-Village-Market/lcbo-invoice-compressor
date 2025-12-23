#!/usr/bin/env python3
"""
PDF Invoice Processor - Removes unnecessary information and creates condensed, readable PDFs
"""

import pdfplumber
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, PageTemplate, Frame
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
from datetime import datetime
import re


class LCBOInvoiceProcessor:
    """Process LCBO invoices to create condensed, readable PDFs"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.products = []
        self.invoice_info = {}
        # Columns to display in output
        self.columns = ['product_number', 'size_ml', 'description', 'dep', 'ordered', 'shipped']
        
    def extract_invoice_info(self, pdf):
        """Extract invoice metadata"""
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        
        # Extract order number
        order_match = re.search(r'ORDER # (\d+)', text)
        self.invoice_info['order_number'] = order_match.group(1) if order_match else 'N/A'
        
        # Extract order date
        date_match = re.search(r'ORDER DATE (\d{1,2}/\d{1,2}/\d{4})', text)
        self.invoice_info['order_date'] = date_match.group(1) if date_match else 'N/A'
        
        # Extract customer info
        if 'Customer #:' in text:
            customer_match = re.search(r'Customer #: (\d+)', text)
            self.invoice_info['customer_number'] = customer_match.group(1) if customer_match else 'N/A'
        
        # Extract customer name - look for text after "SOLD TO RECIPIENT"
        lines = text.split('\n')
        customer_name = None
        for i, line in enumerate(lines):
            if 'SOLD TO' in line and 'RECIPIENT' in line:
                # Next non-empty line after SOLD TO RECIPIENT header is customer name
                for j in range(i+1, min(i+4, len(lines))):
                    if lines[j].strip() and not any(x in lines[j] for x in ['SHIP', 'Customer', 'RECIPIENT']):
                        customer_name = lines[j].strip()
                        break
                break
        
        self.invoice_info['customer_name'] = customer_name if customer_name else 'N/A'
        
        # Extract HST info
        hst_match = re.search(r'HST (\d+)%', text)
        self.invoice_info['hst_percent'] = hst_match.group(1) if hst_match else '13'
        
    def extract_products(self, pdf):
        """Extract product information from all pages"""
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            lines = text.split('\n')
            
            in_products_section = False
            used_lines = set()  # Track which lines we've already used
            
            for i, line in enumerate(lines):
                # Start reading products when we see the header row
                if 'PRODUCT #' in line and 'SIZE (mL)' in line:
                    in_products_section = True
                    continue
                
                # Stop at footer
                if 'CUSTOMER COPY' in line or 'PAGE' in line:
                    in_products_section = False
                    continue
                
                if in_products_section and line.strip():
                    stripped = line.strip()
                    # Check if this line is a product data line (starts with product number)
                    if stripped and stripped[0].isdigit():
                        # Skip if we've already used this line
                        if i in used_lines:
                            continue
                        
                        # Collect any preceding non-data lines as part of description
                        preceding_desc = ""
                        j = i - 1
                        
                        # First determine size_end_idx and check for inline description
                        parts = stripped.split()
                        has_inline_description = False
                        size_end_idx = 1
                        if len(parts) > 2 and parts[2] == 'x':
                            size_end_idx = 4
                        else:
                            size_end_idx = 2
                        
                        # Now check if there's description between size and DEP
                        if len(parts) > size_end_idx:
                            for part in parts[size_end_idx:]:
                                try:
                                    val = float(part)
                                    if 0.05 < val < 3.0:  # DEP value (can be up to 2.40+)
                                        # Count text parts between size and DEP
                                        text_count = 0
                                        for p in parts[size_end_idx:]:
                                            try:
                                                float(p)
                                                break
                                            except:
                                                text_count += 1
                                        if text_count > 0:
                                            has_inline_description = True
                                        break
                                except ValueError:
                                    pass
                        
                        # Only look at the immediately preceding line for description if NO inline description
                        if not has_inline_description and j >= 0 and j not in used_lines:
                            prev_line = lines[j].strip()
                            # Only use preceding line if:
                            # 1. Previous line is not a data line (product number at start)
                            # 2. Previous line is not a header
                            if (prev_line and not prev_line[0].isdigit() and 
                                not any(col in prev_line for col in ['PRODUCT #', 'SIZE (mL)', 'DESCRIPTION', 'ORDERED', 'SHIPPED', 'RETAIL', 'DISCOUNT', 'EXTENDED', 'CUSTOMER COPY', 'PAGE'])):
                                preceding_desc = prev_line
                                used_lines.add(j)
                        
                        # Only look for following description if current line doesn't have one
                        following_desc = ""
                        if not has_inline_description:
                            j = i + 1
                            if j < len(lines) and j not in used_lines:
                                next_line = lines[j].strip()
                                # Only take following line if it's not empty, not a data line, not a header
                                if (next_line and not next_line[0].isdigit() and len(next_line) < 100 and
                                    not any(col in next_line for col in ['PRODUCT #', 'SIZE (mL)', 'DESCRIPTION', 'ORDERED', 'SHIPPED', 'RETAIL', 'DISCOUNT', 'EXTENDED', 'CUSTOMER COPY', 'PAGE'])):
                                    following_desc = next_line
                                    used_lines.add(j)
                        
                        product = self.parse_product_line(line, preceding_desc, following_desc)
                        if product:
                            self.products.append(product)
                        used_lines.add(i)
    
    def parse_product_line(self, line, preceding_desc="", following_desc=""):
        """Parse a product line from invoice"""
        # Pattern: PRODUCT# SIZE DESC ... DEP ORDERED SHIPPED [prices...]
        parts = line.split()
        
        if not parts or not parts[0].isdigit():
            return None
        
        try:
            product = {
                'product_number': parts[0],
                'size_ml': '',
                'description': '',
                'dep': '',
                'ordered': 0,
                'shipped': 0
            }
            
            # Size is in parts[1], may be single number or "X x YYY" format
            size_parts = []
            size_end_idx = 1
            
            # Handle "x" in sizes (e.g., "8 x 355")
            if len(parts) > 2 and parts[2] == 'x':
                product['size_ml'] = f"{parts[1]} x {parts[3]}"
                size_end_idx = 4
            else:
                product['size_ml'] = parts[1]
                size_end_idx = 2
            
            # Now extract description - goes until we hit DEP value
            # DEP values are typically: 0.10, 0.20, 0.60, 0.80, 1.20, etc.
            desc_parts = []
            dep_idx = -1
            
            for i in range(size_end_idx, len(parts)):
                try:
                    val = float(parts[i])
                    # Check if this is likely a DEP value (0.05 to 3.0)
                    if 0.05 < val < 3.0:
                        product['dep'] = parts[i]
                        dep_idx = i
                        break
                except ValueError:
                    pass
            
            # Description is everything between size and DEP
            if dep_idx > size_end_idx:
                desc_parts = parts[size_end_idx:dep_idx]
            
            # Build description from preceding + current + following
            description_parts = []
            if preceding_desc:
                description_parts.append(preceding_desc.strip())
            if desc_parts:
                description_parts.append(' '.join(desc_parts))
            if following_desc:
                description_parts.append(following_desc.strip())
            
            product['description'] = ' '.join(description_parts) if description_parts else 'Unknown'
            
            # After DEP, we should have: ORDERED SHIPPED [RETAIL DISCOUNT EXTENDED]
            if dep_idx >= 0 and dep_idx + 2 < len(parts):
                try:
                    product['ordered'] = int(float(parts[dep_idx + 1]))
                    product['shipped'] = int(float(parts[dep_idx + 2]))
                except (ValueError, IndexError):
                    pass
            
            return product
        except Exception as e:
            return None
    
    def calculate_totals(self):
        """Calculate order totals"""
        return {
            'item_count': len(self.products)
        }
    
    def process(self):
        """Process the PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            self.extract_invoice_info(pdf)
            self.extract_products(pdf)
        
        return self.invoice_info, self.products
    
    def generate_condensed_pdf(self, output_path):
        """Generate a condensed, readable PDF"""
        doc = SimpleDocTemplate(output_path, pagesize=letter,
                              rightMargin=0.5*inch, leftMargin=0.5*inch,
                              topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Title and invoice info
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                     fontSize=16, textColor=colors.HexColor('#1a1a1a'),
                                     spaceAfter=10, alignment=1)
        
        story.append(Paragraph("LCBO INVOICE SUMMARY", title_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Invoice details in a compact format
        info_data = [
            ['Order #:', self.invoice_info.get('order_number', 'N/A'),
             'Order Date:', self.invoice_info.get('order_date', 'N/A')],
            ['Customer:', self.invoice_info.get('customer_name', 'N/A'),
             'Customer #:', self.invoice_info.get('customer_number', 'N/A')],
        ]
        
        info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1*inch, 1.8*inch])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ROWBACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Sort products by description (alphabetical)
        sorted_products = sorted(self.products, key=lambda p: p['description'].lower())
        
        # Products table - condensed columns
        products_data = [['Received', 'Product #', 'Size (mL)', 'Description', 'DEP', 'Ordered', 'Shipped']]
        
        for product in sorted_products:
            products_data.append([
                '',  # Received checkbox/input left empty
                product['product_number'],
                product['size_ml'],
                product['description'],  # Full description, no truncation
                product['dep'],
                str(product['ordered']),
                str(product['shipped'])
            ])
        
        # Create products table with appropriate column widths
        col_widths = [0.6*inch, 0.8*inch, 0.8*inch, 3.4*inch, 0.5*inch, 0.7*inch, 0.7*inch]
        products_table = Table(products_data, colWidths=col_widths)
        
        # Build table style with alternating row colors
        table_styles = [
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9.5),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Received column
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),   # Product # column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Size column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]
        
        # Add alternating row colors and make rows bold where Ordered != Shipped
        for row_idx in range(1, len(products_data)):
            # Alternating background colors
            if row_idx % 2 == 0:
                table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#F0F0F0')))
            else:
                table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white))
            
            # Make row bold if Ordered != Shipped
            product = sorted_products[row_idx - 1]
            if product['ordered'] != product['shipped']:
                table_styles.append(('FONT', (0, row_idx), (-1, row_idx), 'Helvetica-Bold', 7.5))
        
        products_table.setStyle(TableStyle(table_styles))
        
        story.append(products_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Footer
        totals = self.calculate_totals()
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                      fontSize=7, textColor=colors.grey,
                                      alignment=1)
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>"
            f"Total items: {totals['item_count']}",
            footer_style
        ))
        
        doc.build(story)
        
        # Add page numbers using PyPDF2
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas as pdfcanvas
            from io import BytesIO
            
            # Read the generated PDF
            reader = PdfReader(output_path)
            writer = PdfWriter()
            total_pages = len(reader.pages)
            
            # Add page numbers to each page
            for page_num, page in enumerate(reader.pages, 1):
                # Create a new page with the page number
                packet = BytesIO()
                can = pdfcanvas.Canvas(packet, pagesize=letter)
                can.setFont("Helvetica", 9)
                can.drawRightString(7.75*inch, 10.75*inch, f"{page_num} / {total_pages}")
                can.save()
                
                # Read the overlay
                packet.seek(0)
                overlay = PdfReader(packet)
                overlay_page = overlay.pages[0]
                
                # Merge with original page
                page.merge_page(overlay_page)
                writer.add_page(page)
            
            # Write out the final PDF
            with open(output_path, 'wb') as f:
                writer.write(f)
        except Exception as e:
            pass  # If page number addition fails, continue with PDF without page numbers


def main():
    """Main processing function"""
    import sys
    
    # Get PDF file
    pdf_file = "Nov 19, 2025 invoice.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Error: {pdf_file} not found")
        sys.exit(1)
    
    print(f"Processing: {pdf_file}")
    print("=" * 60)
    
    # Process PDF
    processor = LCBOInvoiceProcessor(pdf_file)
    invoice_info, products = processor.process()
    
    print(f"Order #: {invoice_info.get('order_number')}")
    print(f"Date: {invoice_info.get('order_date')}")
    print(f"Customer: {invoice_info.get('customer_name')}")
    print(f"Items: {len(products)}")
    
    totals = processor.calculate_totals()
    print(f"Total items: {totals['item_count']}")
    
    # Generate condensed PDF
    output_file = pdf_file.replace('.pdf', '_condensed.pdf')
    print(f"\nGenerating condensed PDF: {output_file}")
    processor.generate_condensed_pdf(output_file)
    
    print(f"✓ PDF created successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
