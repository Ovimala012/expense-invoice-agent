# Week 2: Document MCP server

Goal: an MCP server that reads invoice PDFs and returns the fields the agent needs to check them against the ledger.

## What's here
- `mcp_servers/documents/extract.py`
  - `read_pdf_text(path)` - pulls the text out of every page with pypdf
  - `extract_invoice_fields(text)` - finds invoice number, vendor ID, vendor name, date, department, total and line items with label matching
  - Missing required fields are listed in `missing_fields`, never guessed
  - If the line items don't add up to the printed total, it adds a warning
- `mcp_servers/documents/server.py` - the MCP server with 2 tools:
  - `list_documents` - which invoice PDFs are waiting?
  - `extract_invoice(filename)` - fields for one PDF; only files inside `data/invoices` can be read
- `scripts/make_sample_invoices.py` - creates 6 synthetic invoices, each testing one check:

  | File | What the agent should do |
  |---|---|
  | 01_clean.pdf | Pass every check, record as pending |
  | 02_duplicate.pdf | Flag: INV-1001 is already paid |
  | 03_unapproved_vendor.pdf | Flag: vendor V003 is not approved |
  | 04_over_policy.pdf | Flag: $7,200 is over Engineering's $5,000 single-invoice limit |
  | 05_over_budget.pdf | Flag: $1,500 is over Marketing's remaining $1,100 budget |
  | 06_total_mismatch.pdf | Flag: line items add up to $690 but the total says $790 |

  These 6 files become the first test cases for the Week 5 evaluation suite.
- `scripts/try_documents.py` - starts the server and extracts every sample, like an agent would
- `tests/` - 15 pytest tests covering the ledger and extraction

## Run it (Windows, VS Code terminal)
```
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\make_sample_invoices.py
python scripts\try_documents.py
python -m pytest -q
```

## Be ready to explain in an interview
- Why the agent gets tools through MCP instead of direct database access (separation, least privilege, reusable by any agent)
- Why `record_invoice` only ever writes *pending* (payment always needs a human)
- Why extraction reports missing fields instead of guessing (a wrong vendor ID is worse than a flagged one)
- Why `extract_invoice` is locked to `data/invoices` (an agent must not be able to read arbitrary files)

## Your exercises this week
1. Add an invoice with no Vendor ID line to `make_sample_invoices.py` and check that `missing_fields` catches it.
2. Add a `due_date` field to the samples and the extractor, with a test.
3. Commit after each exercise with a clear message.

## Next: Week 3
A LangGraph agent (Azure OpenAI) that calls both MCP servers: extract -> check vendor -> check duplicate -> check policy -> record as pending or flag with a reason.
