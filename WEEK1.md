# Week 1: Ledger MCP server

Goal: an MCP server that exposes the company ledger as tools an AI agent can call.

## What's here
- `mcp_servers/ledger/db.py` - a small SQLite ledger with synthetic vendors, budgets and invoices
- `mcp_servers/ledger/server.py` - the MCP server with 4 tools:
  - `get_vendor` - is this vendor approved?
  - `get_budget` - how much budget is left?
  - `check_duplicate_invoice` - was this invoice already entered?
  - `record_invoice` - save a new invoice as *pending* (payment always needs a human)
- `scripts/try_ledger.py` - starts the server and calls each tool, like an agent would

## Run it (Windows, VS Code terminal)
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\try_ledger.py
```
You should see the 4 tool names and a result for each call.

## Your exercises this week
1. Add a tool `list_pending_invoices(department)` that returns pending invoices.
2. Add a `policy` table (max single invoice per department) and a `check_policy` tool.
3. Make `record_invoice` refuse unapproved vendors.
4. Commit after each exercise with a clear message.
