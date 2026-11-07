"""Tests for the ledger tools. Each test gets a fresh database in a temp folder."""
import pytest

from mcp_servers.ledger import db, server


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "ledger.db")
    db.init_db()


def test_unapproved_vendor_is_flagged():
    assert server.get_vendor("V003")["approved"] is False


def test_duplicate_invoice_is_detected():
    assert server.check_duplicate_invoice("V001", "INV-1001")["duplicate"] is True


def test_record_invoice_refuses_unapproved_vendor():
    result = server.record_invoice("V003", "INV-9", "Marketing", 100.0)
    assert result == {"recorded": False, "reason": "vendor is not approved for payment"}


def test_record_invoice_refuses_unknown_vendor():
    assert server.record_invoice("V999", "INV-9", "Marketing", 100.0)["reason"] == "unknown vendor"


def test_record_invoice_refuses_duplicates():
    assert server.record_invoice("V001", "INV-1001", "Engineering", 1250.0)["reason"] == "duplicate invoice"


def test_recorded_invoice_is_pending_and_listed():
    assert server.record_invoice("V002", "INV-2001", "Engineering", 980.0) == {"recorded": True, "status": "pending"}
    pending = server.list_pending_invoices("Engineering")
    assert pending["count"] == 1 and pending["invoices"][0]["invoice_number"] == "INV-2001"


def test_policy_blocks_amount_over_single_invoice_limit():
    result = server.check_policy("Engineering", 7200.0)
    assert result["allowed"] is False and "single-invoice limit" in result["reasons"][0]


def test_policy_blocks_amount_over_remaining_budget():
    result = server.check_policy("Marketing", 1500.0)  # limit 2000, but only 1100 left this month
    assert result["allowed"] is False and "remaining budget" in result["reasons"][0]


def test_policy_allows_normal_amount():
    assert server.check_policy("Engineering", 1800.0)["allowed"] is True


def test_unknown_department_has_no_policy():
    assert server.check_policy("Legal", 10.0)["allowed"] is False
