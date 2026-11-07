"""Read text out of invoice PDFs and pull out the fields the agent needs.

Week 2 uses simple label matching, which works for the synthetic invoices in data/invoices.
In Week 3 the agent can fall back to the LLM for messy, real-world layouts.
"""
import re
from pathlib import Path

from pypdf import PdfReader

REQUIRED_FIELDS = ["invoice_number", "vendor_id", "department", "total"]

# label in the document -> field name
_PATTERNS = {
    "invoice_number": r"Invoice\s*(?:Number|No\.?|#)\s*:?\s*([A-Z0-9-]+)",
    "vendor_id": r"Vendor\s*ID\s*:?\s*([A-Z0-9-]+)",
    "vendor_name": r"Vendor\s*:\s*([^\n]+)",
    "invoice_date": r"(?:Invoice\s*)?Date\s*:?\s*(\d{4}-\d{2}-\d{2})",
    "department": r"(?:Bill\s*To\s*)?Department\s*:?\s*([A-Za-z &]+?)\s*$",
    "total": r"Total\s*(?:Due)?\s*:?\s*\$?\s*([\d,]+\.\d{2})",
}

_LINE_ITEM = re.compile(r"^(.+?)\s+(\d+)\s+\$?([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s*$")


def read_pdf_text(path: Path) -> str:
    """Return the text of every page in the PDF, joined with newlines."""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _money(value: str) -> float:
    return float(value.replace(",", ""))


def extract_invoice_fields(text: str) -> dict:
    """Pull invoice fields out of plain text. Missing fields are listed, never guessed."""
    fields: dict = {}
    for name, pattern in _PATTERNS.items():
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            fields[name] = match.group(1).strip()
    if "total" in fields:
        fields["total"] = _money(fields["total"])

    line_items = []
    for line in text.splitlines():
        m = _LINE_ITEM.match(line.strip())
        if m and not line.lower().startswith(("total", "subtotal")):
            line_items.append(
                {"description": m.group(1).strip(), "quantity": int(m.group(2)),
                 "unit_price": _money(m.group(3)), "amount": _money(m.group(4))}
            )
    fields["line_items"] = line_items

    missing = [f for f in REQUIRED_FIELDS if f not in fields]
    warnings = []
    if line_items and "total" in fields:
        items_sum = round(sum(i["amount"] for i in line_items), 2)
        if abs(items_sum - fields["total"]) > 0.01:
            warnings.append(f"line items add up to {items_sum:.2f} but the total says {fields['total']:.2f}")
    fields["missing_fields"] = missing
    fields["warnings"] = warnings
    fields["complete"] = not missing
    return fields
