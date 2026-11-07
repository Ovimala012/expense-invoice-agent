# Expense & Invoice Agent

An AI agent that reads invoices and receipts, checks them against a ledger and spending policy, and drafts approvals or flags problems, with a human approving anything risky.

Built to show production-style agent engineering: MCP tools, orchestration, human-in-the-loop control and measurable reliability.

## Architecture

```
Invoices / receipts (PDF)
        |
  MCP servers  ->  Document store (PDF extraction)
               ->  Ledger (PostgreSQL)
               ->  Payments API (mock)
        |
  LangGraph agent (Azure OpenAI)
        |
  Policy checks + guardrails (spend limits, duplicates)
        |
  Human approval step for payments over a threshold
        |
  Evaluation suite (DeepEval, LLM-as-judge, task success) + tracing
```

## Build plan

- [x] Week 1: MCP server for the ledger (SQLite for now; PostgreSQL later)
- [x] Week 2: MCP server for document extraction
- [x] Week 3: LangGraph agent wired to the MCP tools
- [x] Week 4: Human approval step and spend-limit guardrails (approval over $1,000, spend limits, duplicate and vendor checks)
- [ ] Week 5: Evaluation suite and tracing
- [ ] Week 6: Demo video, results and write-up

## Run the tests

```
pip install -r requirements.txt
python scripts\make_sample_invoices.py
python -m pytest -q

# run the agent on all sample invoices
python scripts\run_agent.py

# same thing through the LangGraph graph
pip install -r requirements-agent.txt
python scripts\run_agent.py --graph
```

## Tech

Python · MCP · pypdf · pytest · LangGraph · Azure OpenAI · PostgreSQL · DeepEval · Docker

All data in this project is synthetic.
