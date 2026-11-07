# Week 1: Ledger MCP server

Goal: an MCP server that exposes the company ledger as tools an AI agent can call.

## What's here
- `mcp_servers/ledger/db.py` - a small SQLite ledger with synthetic vendors, budgets and invoices
- `mcp_servers/ledger/server.py` - the MCP server with 6 tools:
  - `get_vendor` - is this vendor approved?
  - `get_budget` - how much budget is left?
  - `check_duplicate_invoice` - was this invoice already entered?
  - `list_pending_invoices` - which invoices are waiting for a human?
  - `check_policy` - is this amount within the department's limit and remaining budget?
  - `record_invoice` - save a new invoice as *pending* (payment always needs a human); refuses unknown/unapproved vendors and duplicates
- `scripts/try_ledger.py` - starts the server and calls each tool, like an agent would

## Run it (Windows, VS Code terminal)
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\try_ledger.py
```
You should see the 6 tool names and a result for each call.

## Exercises (done)
- [x] `list_pending_invoices(department)` returns a department's pending invoices.
- [x] `policy` table (max single invoice per department) and a `check_policy` tool that also checks remaining budget.
- [x] `record_invoice` refuses unknown and unapproved vendors.
- Tests for all of these are in `tests/test_ledger.py`.
