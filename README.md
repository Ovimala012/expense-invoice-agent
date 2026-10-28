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

- [ ] Week 1: MCP server for the ledger (PostgreSQL)
- [ ] Week 2: MCP server for document extraction
- [ ] Week 3: LangGraph agent wired to the MCP tools
- [ ] Week 4: Human approval step and spend-limit guardrails
- [ ] Week 5: Evaluation suite and tracing
- [ ] Week 6: Demo video, results and write-up

## Tech

Python · MCP · LangGraph · Azure OpenAI · PostgreSQL · DeepEval · Docker

All data in this project is synthetic.
