#!/usr/bin/env python3
"""
Wholesale cost calculator for Quick Order PDFs.
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

import pdfplumber


@dataclass
class WholesaleItemRecord:
    item: str
    qty: int
    wholesale_price: float | None = None
    units: int | None = None
    n_count: int = 1
    z_ml: float | None = None
    sku_not_found: bool = False


class WholesaleCostCalculator:
    """Parse wholesale quick-order PDFs and compute item costs."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.records: list[WholesaleItemRecord] = []

    @staticmethod
    def _normalize_item(value: str) -> str:
        digits = re.sub(r"\D", "", value)
        normalized = digits.lstrip("0")
        return normalized if normalized else "0"

    @staticmethod
    def _extract_size_components(size_line: str) -> tuple[int, float] | None:
        multi_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:x|×|pk|pack)\s*(\d+(?:\.\d+)?)\s*ml\b",
            size_line,
            re.IGNORECASE,
        )
        if multi_match:
            n_count = int(float(multi_match.group(1)))
            z_ml = float(multi_match.group(2))
            return n_count, z_ml

        ml_match = re.search(r"(\d+(?:\.\d+)?)\s*ml\b", size_line, re.IGNORECASE)
        if ml_match:
            return 1, float(ml_match.group(1))

        l_match = re.search(r"(\d+(?:\.\d+)?)\s*l\b", size_line, re.IGNORECASE)
        if l_match:
            return 1, float(l_match.group(1)) * 1000.0

        return None

    @staticmethod
    def _get_deposit(z_ml: float, n_count: int) -> float:
        unit_deposit = 0.2 if z_ml > 610 else 0.1
        return unit_deposit * n_count

    def parse_quick_order(self) -> list[WholesaleItemRecord]:
        """Parse a Quick Order PDF into item records."""
        with pdfplumber.open(self.pdf_path) as pdf:
            lines = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines.extend([line.strip() for line in text.split("\n") if line.strip()])

        records: list[WholesaleItemRecord] = []
        current: WholesaleItemRecord | None = None

        for line in lines:
            qty_line_match = re.fullmatch(r"(\d+)\s+(\d+)\s+Remove", line)
            if qty_line_match:
                if current is not None:
                    records.append(current)
                current = WholesaleItemRecord(
                    item=self._normalize_item(qty_line_match.group(1)),
                    qty=int(qty_line_match.group(2)),
                )
                continue

            if current is None:
                continue

            if re.search(r"sku was not found", line, re.IGNORECASE):
                current.sku_not_found = True
                continue

            wholesale_match = re.search(r"Wholesale\s+price:\s*\$([\d,]+(?:\.\d{2})?)", line, re.IGNORECASE)
            if wholesale_match:
                current.wholesale_price = float(wholesale_match.group(1).replace(",", ""))
                continue

            lcbo_match = re.search(r"LCBO#:\s*(\d+)", line, re.IGNORECASE)
            if lcbo_match:
                current.item = self._normalize_item(lcbo_match.group(1))
                continue

            units_match = re.search(r"\{\s*(\d+)\s+units\s*\}", line, re.IGNORECASE)
            if units_match:
                current.units = int(units_match.group(1))
                continue

            if current.z_ml is None:
                size_components = self._extract_size_components(line)
                if size_components is not None:
                    current.n_count, current.z_ml = size_components

        if current is not None:
            records.append(current)

        self.records = records
        return records

    def calculate_cost_rows(self, allowed_items: set[str]) -> list[tuple[str, float]]:
        """Compute item cost rows from parsed records."""
        if not self.records:
            self.parse_quick_order()

        output_rows: list[tuple[str, float]] = []

        for record in self.records:
            if record.item not in allowed_items:
                continue
            if record.sku_not_found:
                continue
            if record.wholesale_price is None or record.units is None or record.z_ml is None:
                continue
            if record.qty <= 0 or record.units <= 0:
                continue
            if record.n_count <= 0:
                continue

            price_per_unit = (record.wholesale_price / record.qty) / record.units
            x_value = price_per_unit - self._get_deposit(record.z_ml, record.n_count)
            cost = x_value / 1.13
            output_rows.append((record.item, cost))

        return output_rows

    @staticmethod
    def write_item_cost_csv(output_csv_path: str, rows: list[tuple[str, float]]) -> int:
        """Write item-cost rows to CSV with columns: item, cost."""
        output_path = Path(output_csv_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["item", "cost"])
            for item, cost in rows:
                rounded_cost = Decimal(str(cost)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                writer.writerow([item, f"{rounded_cost:.2f}"])

        return len(rows)
