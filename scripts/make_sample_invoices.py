"""Create synthetic invoice PDFs in data/invoices for testing. All data is made up."""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "data" / "invoices"

# (file, vendor_id, vendor_name, invoice_number, department, date, line items, printed total)
# Each one exercises a different check the agent has to make.
INVOICES = [
    ("01_clean.pdf", "V002", "CloudHost LLC", "INV-3001", "Engineering", "2026-11-02",
     [("Cloud hosting - October", 1, 1800.00)], None),
    ("02_duplicate.pdf", "V001", "Acme Office Supply", "INV-1001", "Engineering", "2026-10-15",
     [("Office chairs", 5, 250.00)], None),
    ("03_unapproved_vendor.pdf", "V003", "Unknown Consulting", "INV-7001", "Marketing", "2026-11-03",
     [("Strategy workshop", 1, 900.00)], None),
    ("04_over_policy.pdf", "V002", "CloudHost LLC", "INV-3002", "Engineering", "2026-11-04",
     [("GPU reserved instances", 3, 2400.00)], None),
    ("05_over_budget.pdf", "V001", "Acme Office Supply", "INV-1050", "Marketing", "2026-11-05",
     [("Trade show booth supplies", 1, 1500.00)], None),
    ("06_total_mismatch.pdf", "V001", "Acme Office Supply", "INV-1051", "Engineering", "2026-11-05",
     [("Printer paper", 10, 45.00), ("Toner", 2, 120.00)], 790.00),
    ("07_small_clean.pdf", "V001", "Acme Office Supply", "INV-1052", "Engineering", "2026-11-06",
     [("Whiteboard markers", 12, 20.00)], None),
]


def draw(path: Path, vendor_id, vendor_name, number, dept, date, items, printed_total) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    y = 740
    def line(text, size=11, gap=18):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(72, y, text)
        y -= gap
    line("INVOICE", 18, 30)
    line(f"Vendor: {vendor_name}")
    line(f"Vendor ID: {vendor_id}")
    line(f"Invoice Number: {number}")
    line(f"Invoice Date: {date}")
    line(f"Bill To Department: {dept}", gap=30)
    line("Description Qty Unit Price Amount")
    total = 0.0
    for desc, qty, price in items:
        amount = qty * price
        total += amount
        line(f"{desc} {qty} ${price:,.2f} ${amount:,.2f}")
    y -= 12
    line(f"Total Due: ${printed_total if printed_total is not None else total:,.2f}", 12)
    c.save()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for row in INVOICES:
        draw(OUT / row[0], *row[1:])
        print("wrote", OUT / row[0])
