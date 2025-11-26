"""
Configuration template for PDF Processor customization
Copy this file as config.py and modify values as needed
"""

# PDF Output Settings
PDF_CONFIG = {
    # Page size: 'letter', 'A4'
    'page_size': 'letter',
    
    # Margins (in inches)
    'margin_top': 0.5,
    'margin_bottom': 0.5,
    'margin_left': 0.5,
    'margin_right': 0.5,
    
    # Font sizes
    'title_font_size': 16,
    'header_font_size': 9,
    'table_header_font_size': 8,
    'table_body_font_size': 7.5,
    'footer_font_size': 7,
    
    # Colors (hex format)
    'title_color': '#1a1a1a',
    'header_background': '#4472C4',
    'header_text': '#ffffff',
    'table_border': '#808080',
    'info_background': '#d3d3d3',
    'totals_background': '#E7E6E6',
}

# Table Column Configuration
COLUMNS = {
    'product_description': {
        'width': 3.0,  # inches
        'max_length': 40,  # characters
        'align': 'LEFT'
    },
    'size_ml': {
        'width': 0.8,
        'align': 'CENTER'
    },
    'quantity': {
        'width': 0.5,
        'align': 'RIGHT'
    },
    'discount_price': {
        'width': 1.0,
        'align': 'RIGHT',
        'format': '${:.2f}'
    },
    'extended_price': {
        'width': 1.0,
        'align': 'RIGHT',
        'format': '${:.2f}'
    }
}

# Extraction Settings
EXTRACTION = {
    # Regex patterns for data extraction
    'order_number_pattern': r'ORDER # (\d+)',
    'order_date_pattern': r'ORDER DATE (\d{1,2}/\d{1,2}/\d{4})',
    'customer_number_pattern': r'Customer #: (\d+)',
    'hst_percent_pattern': r'HST (\d+)%',
    
    # Default values if not found
    'default_hst_percent': 13,
    'default_currency': '$',
}

# Features to Include
FEATURES = {
    'include_customer_info': True,
    'include_order_metadata': True,
    'include_product_table': True,
    'include_totals': True,
    'include_footer': True,
    'include_timestamp': True,
}

# Output Settings
OUTPUT = {
    # Suffix for condensed files
    'output_suffix': '_condensed',
    
    # Skip already processed files
    'skip_existing': True,
    
    # Verbose output
    'verbose': True,
}
