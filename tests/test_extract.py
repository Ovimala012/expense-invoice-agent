"""Tests for invoice field extraction, on plain text and on the sample PDFs."""
from pathlib import Path

import pytest

from mcp_servers.documents import server
from mcp_servers.documents.extract import extract_invoice_fields

SAMPLE = """INVOICE
Vendor: CloudHost LLC
Vendor ID: V002
Invoice Number: INV-3001
Invoice Date: 2026-11-02
Bill To Department: Engineering
Description Qty Unit Price Amount
Cloud hosting - October 1 $1,800.00 $1,800.00
Total Due: $1,800.00
"""


def test_extracts_all_fields():
    f = extract_invoice_fields(SAMPLE)
    assert (f["invoice_number"], f["vendor_id"], f["department"], f["total"]) == ("INV-3001", "V002", "Engineering", 1800.0)
    assert f["invoice_date"] == "2026-11-02" and f["complete"] is True
    assert f["line_items"] == [{"description": "Cloud hosting - October", "quantity": 1, "unit_price": 1800.0, "amount": 1800.0}]


def test_missing_fields_are_reported_not_guessed():
    f = extract_invoice_fields(SAMPLE.replace("Vendor ID: V002\n", ""))
    assert "vendor_id" not in f and f["missing_fields"] == ["vendor_id"] and f["complete"] is False


def test_total_mismatch_is_warned():
    f = extract_invoice_fields(SAMPLE.replace("Total Due: $1,800.00", "Total Due: $1,900.00"))
    assert f["warnings"] and "1800.00" in f["warnings"][0]


@pytest.mark.skipif(not (server.INVOICE_DIR / "01_clean.pdf").exists(), reason="run scripts/make_sample_invoices.py first")
def test_sample_pdfs_extract_cleanly():
    assert server.list_documents()["count"] >= 6
    assert server.extract_invoice("04_over_policy.pdf")["total"] == 7200.0


def test_cannot_read_outside_invoice_folder():
    assert server.extract_invoice("../ledger.db")["ok"] is False
