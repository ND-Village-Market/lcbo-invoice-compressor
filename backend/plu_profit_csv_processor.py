import csv
import re

import pdfplumber


class PluProfitCSVExtractor:
    """Extract PLU table rows from PDF and output CSV sorted by %Profit."""

    COLUMN_NAMES = [
        'plu',
        'description',
        'vendor_sku',
        'label',
        'price',
        'cost',
        'profit',
        'profit_percent',
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.rows = []

    def _is_noise_line(self, line: str) -> bool:
        if not line:
            return True

        lowered = line.lower().strip()
        if not lowered:
            return True

        noise_prefixes = (
            'plu list with cost and active price',
            'printed:',
            'item group:',
            'price group:',
            'cost group:',
            'from plu:',
            '# description vendor sku',
            'new dundee village market',
        )
        if lowered.startswith(noise_prefixes):
            return True

        if re.fullmatch(r'\d+\s*/\s*\d+', lowered):
            return True

        if re.fullmatch(r'page\s*\d+\s*/\s*\d+', lowered):
            return True

        if re.fullmatch(r'\(\d{3}\)\s*\d{3}-\d{4}', lowered):
            return True

        return False

    def _is_section_heading(self, line: str) -> bool:
        return bool(re.fullmatch(r'\d{1,2}\s+[A-Z][A-Z0-9\s&\-/]+', line.strip()))

    def _normalize_row_text(self, row_text: str) -> str:
        normalized = re.sub(r'\s+', ' ', row_text).strip()
        # Fix wrapped profit percentages like "10. 01".
        normalized = re.sub(r'(\d)\.\s+(\d{1,2})(?=\s|$)', r'\1.\2', normalized)
        return normalized

    def _parse_row(self, row_text: str):
        row_text = self._normalize_row_text(row_text)
        match = re.match(
            r'^(?P<plu>\d{12,14})\s+(?P<body>.+?)\s+\$(?P<price>\d[\d,]*\.\d{2})\s+\$(?P<cost>\d[\d,]*\.\d{2})\s+\$(?P<profit>\d[\d,]*\.\d{2})\s+(?P<profit_percent>-?\d+(?:\.\d+)?)$',
            row_text,
        )
        if not match:
            return None

        body = match.group('body').strip()
        tokens = body.split()
        if not tokens:
            return None

        vendor_index = None
        for idx in range(len(tokens) - 1, -1, -1):
            if re.fullmatch(r'\d{5,6}', tokens[idx]):
                vendor_index = idx
                break

        if vendor_index is None:
            return None

        description = ' '.join(tokens[:vendor_index]).strip()
        vendor_sku = tokens[vendor_index]
        label = ' '.join(tokens[vendor_index + 1:]).strip()
        if not description:
            return None

        return {
            'plu': match.group('plu'),
            'description': description,
            'vendor_sku': vendor_sku,
            'label': label,
            'price': match.group('price'),
            'cost': match.group('cost'),
            'profit': match.group('profit'),
            'profit_percent': match.group('profit_percent'),
        }

    def extract_rows(self):
        row_candidates = []
        current_row = ''

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ''
                for raw_line in text.split('\n'):
                    line = raw_line.strip()
                    if self._is_noise_line(line):
                        continue
                    if self._is_section_heading(line):
                        continue

                    if re.match(r'^\d{12,14}\b', line):
                        if current_row:
                            row_candidates.append(current_row)
                        current_row = line
                    elif current_row:
                        current_row = f'{current_row} {line}'

        if current_row:
            row_candidates.append(current_row)

        rows = []
        for candidate in row_candidates:
            parsed = self._parse_row(candidate)
            if parsed:
                rows.append(parsed)

        rows.sort(key=lambda row: float(row['profit_percent']), reverse=True)
        self.rows = rows
        return rows

    def write_csv(self, output_dir: str, base_name: str) -> str:
        if not self.rows:
            self.extract_rows()

        output_filename = f'{base_name}_plu_profit_sorted.csv'
        output_path = f'{output_dir}/{output_filename}'

        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=self.COLUMN_NAMES)
            writer.writeheader()
            writer.writerows(self.rows)

        return output_filename