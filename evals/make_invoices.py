"""Writes one PDF per evaluation case into evals/invoices. All data is synthetic."""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from evals.cases import CASES, STANDARD

OUT = Path(__file__).resolve().parent / "invoices"


def draw(path: Path, case: dict) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    if case.get("scanned"):  # a page with only shapes and no text layer, like a scanned image
        c.rect(72, 500, 400, 200, fill=1)
        c.save()
        return
    labels = case.get("labels", STANDARD)
    y = 740

    def line(text, size=11, gap=18):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(72, y, text)
        y -= gap

    line("INVOICE", 18, 30)
    line(f"Vendor: {case['vendor']}")
    if case["vendor_id"]:
        line(f"Vendor ID: {case['vendor_id']}")
    line(f"{labels['number']}: {case['number']}")
    line(f"{labels['date']}: 2026-11-06")
    line(f"{labels['dept']}: {case['dept']}", gap=30)
    line("Description Qty Unit Price Amount")
    total = 0.0
    for desc, qty, price in case["items"]:
        total += qty * price
        line(f"{desc} {qty} ${price:,.2f} ${qty * price:,.2f}")
    y -= 12
    line(f"{labels['total']}: ${case.get('total', total):,.2f}", 12)
    c.save()


def make_all() -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    names = []
    for case in CASES:
        name = f"{case['id']}.pdf"
        draw(OUT / name, case)
        names.append(name)
    return names


if __name__ == "__main__":
    for n in make_all():
        print("wrote", OUT / n)
