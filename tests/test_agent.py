"""End-to-end tests: the agent talks to the real MCP servers over stdio, using a throwaway ledger."""
import asyncio

import pytest

from agent import llm, workflow
from agent.tools import Toolbox
from mcp_servers.documents.server import INVOICE_DIR
from mcp_servers.ledger import db

# What a careful accounts-payable clerk would do with each sample invoice.
EXPECTED = {
    "01_clean.pdf": ("needs_approval", None),
    "02_duplicate.pdf": ("flagged", "already in the ledger"),
    "03_unapproved_vendor.pdf": ("flagged", "not approved"),
    "04_over_policy.pdf": ("flagged", "single-invoice limit"),
    "05_over_budget.pdf": ("flagged", "remaining budget"),
    "06_total_mismatch.pdf": ("flagged", "line items add up"),
    "07_small_clean.pdf": ("ready_to_record", None),
}

pytestmark = pytest.mark.skipif(not (INVOICE_DIR / "07_small_clean.pdf").exists(),
                                reason="run scripts/make_sample_invoices.py first")


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "ledger.db"
    monkeypatch.setenv("LEDGER_DB_PATH", str(path))  # the MCP server subprocesses inherit this
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    return path


async def _run(fn):
    async with Toolbox() as tools:
        return await fn(tools)


def test_every_sample_gets_the_expected_decision(ledger):
    async def go(tools):
        return {name: await workflow.run_checks(name, tools) for name in EXPECTED}

    states = asyncio.run(_run(go))
    for name, (decision, reason) in EXPECTED.items():
        state = states[name]
        assert state.decision == decision, (name, state.findings)
        if reason:
            assert any(reason in f for f in state.findings), (name, state.findings)
        else:
            assert state.findings == [], (name, state.findings)


def test_approved_invoice_is_recorded_as_pending(ledger):
    async def go(tools):
        state = await workflow.run_checks("01_clean.pdf", tools)
        state = await workflow.record(state, tools)  # what happens after a human says yes
        return state, await tools.call("list_pending_invoices", department="Engineering")

    state, pending = asyncio.run(_run(go))
    assert state.decision == "recorded"
    assert [i["invoice_number"] for i in pending["invoices"]] == ["INV-3001"]


def test_flagged_invoice_is_never_recorded(ledger):
    async def go(tools):
        await workflow.run_checks("03_unapproved_vendor.pdf", tools)
        return tools.calls, await tools.call("list_pending_invoices", department="Marketing")

    calls, pending = asyncio.run(_run(go))
    assert "record_invoice" not in [c["tool"] for c in calls]
    assert pending["count"] == 0


def test_explanation_mentions_every_finding(ledger):
    async def go(tools):
        return await workflow.run_checks("04_over_policy.pdf", tools)

    state = asyncio.run(_run(go))
    text = llm.explain(state)  # template mode: no Azure key in tests
    assert text.startswith("Flagged INV-3002") and "single-invoice limit" in text
