#!/usr/bin/env python3
"""
Step 1 SKU extractor for PLU list PDFs.
"""

import csv
import re
from pathlib import Path

import pdfplumber


class SupplierCSVExtractor:
    """Extract vendor SKU values from PLU list PDFs and export CSV."""

    MAX_ROWS_PER_CSV = 250

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.suppliers = []

    @staticmethod
    def _is_noise_line(line: str) -> bool:
        if not line:
            return True

        lowered = line.lower().strip()
        if not lowered:
            return True

        noise_prefixes = (
            "plu list with cost and active price",
            "printed:",
            "item group:",
            "price group:",
            "cost group:",
            "from plu:",
            "# description vendor sku",
            "new dundee village market",
        )
        if lowered.startswith(noise_prefixes):
            return True

        if re.fullmatch(r"\d+\s*/\s*\d+", lowered):
            return True

        if re.fullmatch(r"page\s*\d+\s*/\s*\d+", lowered):
            return True

        if re.fullmatch(r"\(\d{3}\)\s*\d{3}-\d{4}", lowered):
            return True

        return False

    @staticmethod
    def _is_section_heading(line: str) -> bool:
        return bool(re.fullmatch(r"\d{1,2}\s+[A-Z][A-Z0-9\s&\-/]+", line.strip()))

    @staticmethod
    def _normalize_row_text(row_text: str) -> str:
        normalized = re.sub(r"\s+", " ", row_text).strip()
        normalized = re.sub(r"(\d)\.\s+(\d{1,2})(?=\s|$)", r"\1.\2", normalized)
        return normalized

    def _extract_supplier_from_row(self, row_text: str) -> str | None:
        row_text = self._normalize_row_text(row_text)
        match = re.match(
            r"^(?P<plu>\d{12,14})\s+(?P<body>.+?)\s+\$(?P<price>\d[\d,]*\.\d{2})\s+\$(?P<cost>\d[\d,]*\.\d{2})\s+\$(?P<profit>\d[\d,]*\.\d{2})\s+(?P<profit_percent>-?\d+(?:\.\d+)?)$",
            row_text,
        )
        if not match:
            return None

        body = match.group("body").strip()
        tokens = body.split()
        if not tokens:
            return None

        for idx in range(len(tokens) - 1, -1, -1):
            if re.fullmatch(r"\d{5,6}", tokens[idx]):
                return tokens[idx]

        return None

    def extract_suppliers(self) -> list[str]:
        """Extract vendor SKUs from all PLU rows in the PDF."""
        row_candidates: list[str] = []
        current_row = ""

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for raw_line in text.split("\n"):
                    line = raw_line.strip()
                    if self._is_noise_line(line):
                        continue
                    if self._is_section_heading(line):
                        continue

                    if re.match(r"^\d{12,14}\b", line):
                        if current_row:
                            row_candidates.append(current_row)
                        current_row = line
                    elif current_row:
                        current_row = f"{current_row} {line}"

        if current_row:
            row_candidates.append(current_row)

        extracted: list[str] = []
        for row_text in row_candidates:
            vendor_sku = self._extract_supplier_from_row(row_text)
            if vendor_sku is not None:
                extracted.append(vendor_sku)

        self.suppliers = extracted
        return extracted

    def generate_csv(self, output_csv_path: str) -> int:
        """Generate CSV with columns: sku, qty."""
        if not self.suppliers:
            self.extract_suppliers()

        output_path = Path(output_csv_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["sku", "qty"])
            for supplier in self.suppliers:
                writer.writerow([supplier, 1])

        return len(self.suppliers)

    def generate_chunked_csvs(self, output_dir: str, base_name: str) -> list[str]:
        """Generate 1+ CSV files with at most MAX_ROWS_PER_CSV rows each."""
        if not self.suppliers:
            self.extract_suppliers()

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not self.suppliers:
            single_name = f"{base_name}_supplier_skus.csv"
            self.generate_csv(str(output_path / single_name))
            return [single_name]

        if len(self.suppliers) <= self.MAX_ROWS_PER_CSV:
            single_name = f"{base_name}_supplier_skus.csv"
            self.generate_csv(str(output_path / single_name))
            return [single_name]

        file_names: list[str] = []
        chunks = [
            self.suppliers[i : i + self.MAX_ROWS_PER_CSV]
            for i in range(0, len(self.suppliers), self.MAX_ROWS_PER_CSV)
        ]

        for idx, chunk in enumerate(chunks, start=1):
            file_name = f"{base_name}_supplier_skus_part_{idx:03d}.csv"
            file_path = output_path / file_name
            with file_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["sku", "qty"])
                for supplier in chunk:
                    writer.writerow([supplier, 1])
            file_names.append(file_name)

        return file_names
