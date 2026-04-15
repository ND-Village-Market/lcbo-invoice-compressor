#!/usr/bin/env python3
"""
Supplier CSV extractor for item-list PDFs.
"""

import csv
import re
from pathlib import Path

import pdfplumber


class SupplierCSVExtractor:
    """Extract supplier numbers from item list PDFs and export CSV."""

    HEADER_MARKERS = ("PLU #", "Supplier #", "Qty/Case")

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.suppliers = []

    @staticmethod
    def _normalize_supplier(raw_value: str) -> str | None:
        """Keep digits only and strip leading zeros."""
        digits_only = re.sub(r"\D", "", raw_value)
        if not digits_only:
            return None

        normalized = digits_only.lstrip("0")
        return normalized if normalized else "0"

    @staticmethod
    def _extract_supplier_from_row(line: str) -> str | None:
        """
        Extract supplier column value from an item row.

        Expected row tail shape resembles:
        <supplier-ish tokens> <qty> <case_cost> <unit_cost>
        """
        # Skip obvious non-row lines.
        if not line or not line[:1].isdigit():
            return None

        tokens = line.split()
        if len(tokens) < 5:
            return None

        money_pattern = re.compile(r"^\d[\d,]*\.\d{2}$")
        if not money_pattern.fullmatch(tokens[-1]):
            return None
        if not money_pattern.fullmatch(tokens[-2]):
            return None
        if not tokens[-3].isdigit():
            return None

        # Walk left from qty to find the closest numeric token used as supplier.
        # Exclude token[0] (PLU) and ignore short numeric description fragments.
        for idx in range(len(tokens) - 4, 0, -1):
            token = tokens[idx]
            if token.isdigit() and 3 <= len(token) <= 8:
                return SupplierCSVExtractor._normalize_supplier(token)

        return None

    def extract_suppliers(self) -> list[str]:
        """Extract suppliers from all item rows in the PDF."""
        extracted = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = [line.strip() for line in text.split("\n") if line.strip()]

                header_idx = -1
                for idx, line in enumerate(lines):
                    if all(marker in line for marker in self.HEADER_MARKERS):
                        header_idx = idx
                        break

                if header_idx == -1:
                    continue

                for line in lines[header_idx + 1 :]:
                    supplier = self._extract_supplier_from_row(line)
                    if supplier is not None:
                        extracted.append(supplier)

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
