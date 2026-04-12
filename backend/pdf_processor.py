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
        self.columns = ['product_number', 'size_ml', 'description', 'ordered', 'shipped']

    def _extract_size_ml(self, text):
        """Extract numeric size in mL from a text fragment."""
        match = re.search(r'(\d+(?:\.\d+)?)\s*ml\b', text, re.IGNORECASE)
        if not match:
            return ''
        value = float(match.group(1))
        return str(int(value)) if value.is_integer() else match.group(1)

    def _extract_case_units(self, lines, start_idx):
        """Extract case unit count from nearby lines in new invoice format."""
        for fwd_idx in range(start_idx + 1, min(start_idx + 10, len(lines))):
            case_match = re.search(r'\{\s*(\d+)\s+units\s*\}', lines[fwd_idx], re.IGNORECASE)
            if case_match:
                return case_match.group(1)
        return ''

    def _parse_fulfilled_by_line(self, line):
        """Parse a 'Fulfilled by' line and return the supplier label, if present."""
        fulfilled_match = re.search(r'Fulfilled\s+by:\s*(.+)$', line, re.IGNORECASE)
        if not fulfilled_match:
            return ''
        fulfilled_by = fulfilled_match.group(1).strip()
        # Trim trailing fulfillment method details to keep the section header concise.
        fulfilled_by = re.sub(r'\s+Fulfillment\s+method\s*:.*$', '', fulfilled_by, flags=re.IGNORECASE).strip()
        return fulfilled_by

    def _clean_product_name_line(self, line):
        """Strip pricing and noise from a product name line."""
        cleaned = re.sub(r'\s+Wholesale\s+price:.*$', '', line, flags=re.IGNORECASE).strip()
        return cleaned

    def _is_noise_line(self, line):
        """Identify non-description lines in the new invoice format."""
        if not line:
            return True
        lowered = line.lower().strip()

        # Skip pure money lines and document/navigation noise.
        if re.fullmatch(r'\$[\d,]+(?:\.\d{2})?', lowered):
            return True

        # Skip standalone date lines like "April 15, 2026".
        if re.fullmatch(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+\d{4}', lowered):
            return True

        noise_tokens = [
            'purchasable only by case',
            'qty. ordered:',
            'estimated delivery date',
            'in progress',
            'unfulfilled',
            'complete',
            'fulfilled by:',
            'fulfillment method:',
            'order total:',
            'order information',
            'delivery option',
            'delivery address',
            'billing address',
            'payment method',
            'lcbo information',
            'how the wholesale price is calculated',
            'status:',
            'date:',
            'order #',
            'print order',
            'items ordered',
        ]

        return any(token in lowered for token in noise_tokens)

    def _extract_products_new_format(self, pdf):
        """Extract products from the new LCBO web-style invoice format."""
        products = []
        current_fulfilled_by = 'LCBO'

        for page in pdf.pages:
            text = page.extract_text() or ''
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            for i, line in enumerate(lines):
                parsed_fulfilled_by = self._parse_fulfilled_by_line(line)
                if parsed_fulfilled_by:
                    current_fulfilled_by = parsed_fulfilled_by
                    continue

                lcbo_match = re.search(r'LCBO#:\s*(\d+)\b(.*)$', line, re.IGNORECASE)
                if not lcbo_match:
                    continue

                product_number = lcbo_match.group(1)
                trailing = lcbo_match.group(2) or ''
                size_ml = self._extract_size_ml(trailing)
                case_units = self._extract_case_units(lines, i)
                if case_units and size_ml:
                    size_ml = f"{case_units} x {size_ml}"
                fulfilled_by = current_fulfilled_by

                # Product name is usually on the line before LCBO#, with possible wrapped lines.
                description_parts = []

                for back_idx in range(max(0, i - 3), i):
                    candidate = lines[back_idx]
                    if self._is_noise_line(candidate):
                        continue

                    # Skip other LCBO lines in case of extraction artifacts.
                    if 'lcbo#:' in candidate.lower():
                        continue

                    cleaned = self._clean_product_name_line(candidate)
                    if cleaned:
                        description_parts.append(cleaned)

                # Ensure we include the base name from a line containing Wholesale price.
                if i - 1 >= 0 and not description_parts:
                    base_line = self._clean_product_name_line(lines[i - 1])
                    if base_line and not self._is_noise_line(base_line):
                        description_parts.append(base_line)

                # De-duplicate while preserving order.
                seen = set()
                deduped_desc = []
                for part in description_parts:
                    if part not in seen:
                        deduped_desc.append(part)
                        seen.add(part)

                description = ' '.join(deduped_desc).strip() or 'Unknown'

                ordered = 0
                shipped = 0

                # Qty is typically after LCBO#, but search within a short forward window.
                for fwd_idx in range(i + 1, min(i + 9, len(lines))):
                    qty_line = lines[fwd_idx]
                    qty_match = re.search(r'Qty\.\s*Ordered:\s*(\d+)(?:\s*\|\s*Fulfilled:\s*(\d+))?', qty_line, re.IGNORECASE)
                    if qty_match:
                        ordered = int(qty_match.group(1))
                        if qty_match.group(2) is not None:
                            shipped = int(qty_match.group(2))
                        else:
                            # Fulfilled quantity is absent in most new-format rows.
                            # Keep parity with prior output behavior by defaulting shipped to ordered.
                            shipped = ordered
                        break

                product = {
                    'product_number': product_number,
                    'size_ml': size_ml,
                    'description': description,
                    'dep': '',
                    'ordered': ordered,
                    'shipped': shipped,
                    'fulfilled_by': fulfilled_by,
                }
                products.append(product)

        # Remove accidental duplicates by product number + description + ordered.
        unique_products = []
        seen_keys = set()
        for product in products:
            key = (
                product['product_number'],
                product['description'],
                product['ordered'],
                product.get('fulfilled_by', ''),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique_products.append(product)

        return unique_products
        
    def extract_invoice_info(self, pdf):
        """Extract invoice metadata"""
        first_page = pdf.pages[0]
        text = first_page.extract_text() or ''
        full_text = '\n'.join((page.extract_text() or '') for page in pdf.pages)
        
        # Extract order number
        order_match = re.search(r'ORDER #\s*(\d+)', text, re.IGNORECASE)
        if not order_match:
            order_match = re.search(r'Order #\s*(\d+)', text, re.IGNORECASE)
        self.invoice_info['order_number'] = order_match.group(1) if order_match else 'N/A'
        
        # Extract order date
        date_match = re.search(r'ORDER DATE\s*(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if not date_match:
            date_match = re.search(r'Date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
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

        # New format fallback: use first name under Delivery Address in the order summary section.
        if not customer_name:
            full_lines = [line.strip() for line in full_text.split('\n') if line.strip()]
            for i, line in enumerate(full_lines):
                if line.lower() == 'delivery address' and i + 1 < len(full_lines):
                    candidate = full_lines[i + 1].strip()
                    if candidate and not self._is_noise_line(candidate):
                        customer_name = candidate
                        break
        
        self.invoice_info['customer_name'] = customer_name if customer_name else 'N/A'
        
        # Extract HST info
        hst_match = re.search(r'HST (\d+)%', text)
        self.invoice_info['hst_percent'] = hst_match.group(1) if hst_match else '13'
        
    def extract_products(self, pdf):
        """Extract product information from all pages"""
        # First, try the legacy tabular parser.
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

        # Fallback: new web-style invoice format (LCBO#: / Qty. Ordered blocks).
        if not self.products:
            self.products = self._extract_products_new_format(pdf)
    
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
                'shipped': 0,
                'fulfilled_by': ''
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
        
        # Build grouped rows by fulfillment source while preserving input order.
        grouped_products = {}
        group_order = []
        for product in self.products:
            fulfilled_by = (product.get('fulfilled_by') or '').strip() or 'LCBO'
            if fulfilled_by not in grouped_products:
                grouped_products[fulfilled_by] = []
                group_order.append(fulfilled_by)
            grouped_products[fulfilled_by].append(product)

        # Products table - grouped by fulfillment source
        products_data = [['Received', 'Product #', 'Size (mL)', 'Description', 'Ordered', 'Shipped', 'Display']]

        section_rows = []
        data_row_products = []
        for fulfilled_by in group_order:
            section_rows.append(len(products_data))
            products_data.append([f"Fulfilled by: {fulfilled_by}", '', '', '', '', '', ''])

            sorted_group_products = sorted(
                grouped_products[fulfilled_by],
                key=lambda p: (p.get('description', '').lower(), p.get('product_number', ''))
            )

            for product in sorted_group_products:
                data_row_products.append(product)
                products_data.append([
                    '',  # Received checkbox/input left empty
                    product['product_number'],
                    product['size_ml'],
                    product['description'],  # Full description, no truncation
                    str(product['ordered']),
                    str(product['shipped']),
                    '',  # Display value left empty
                ])
        
        # Create products table with appropriate column widths
        # Widths aligned to: Received, Product #, Size, Description, Ordered, Shipped, Display
        # Total width remains unchanged for consistent page layout.
        col_widths = [0.6*inch, 0.8*inch, 0.8*inch, 3.3*inch, 0.7*inch, 0.7*inch, 0.6*inch]
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
            ('ALIGN', (6, 0), (6, -1), 'CENTER'),  # Display column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]
        
        # Add alternating row colors and make rows bold where Ordered != Shipped
        data_row_idx = 0
        for row_idx in range(1, len(products_data)):
            if row_idx in section_rows:
                # Highlight the fulfillment section title and span across columns.
                table_styles.append(('SPAN', (0, row_idx), (6, row_idx)))
                table_styles.append(('FONT', (0, row_idx), (0, row_idx), 'Helvetica-Bold', 9))
                table_styles.append(('BACKGROUND', (0, row_idx), (6, row_idx), colors.HexColor('#DCE6F1')))
                table_styles.append(('ALIGN', (0, row_idx), (6, row_idx), 'LEFT'))
                continue

            # Alternating background colors for item rows only.
            if data_row_idx % 2 == 0:
                table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white))
            else:
                table_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#F0F0F0')))

            # Make row bold if Ordered != Shipped.
            product = data_row_products[data_row_idx]
            if product['ordered'] != product['shipped']:
                table_styles.append(('FONT', (0, row_idx), (-1, row_idx), 'Helvetica-Bold', 7.5))

            data_row_idx += 1
        
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
    pdf_file = "./invoices/LCBO Invoice April 7 2026.pdf"
    
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
