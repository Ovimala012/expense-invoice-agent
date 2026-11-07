# Weeks 3-4: The agent, guardrails and human approval

Goal: an agent that takes each invoice PDF, checks it against the ledger through the MCP tools, and either flags it, records it, or stops and asks a person.

## How a decision is made
```
extract -> check_vendor -> check_duplicate -> check_policy -> decide
   decide = flagged          -> explain                    (any check failed)
   decide = needs_approval   -> human_approval -> record   (all checks passed, total >= $1,000)
                                              -> explain   (reviewer said no)
   decide = ready_to_record  -> record -> explain           (all checks passed, under $1,000)
```

## What's here
- `agent/tools.py` - `Toolbox` opens both MCP servers (ledger, documents) and routes each tool call; it logs every call in `tools.calls` for tracing and evaluation in Week 5
- `agent/workflow.py` - each step above as a small async function; all money decisions live here, in code
- `agent/llm.py` - writes the 1-2 sentence explanation for the reviewer with Azure OpenAI, or a template when no key is set; it can never change the decision
- `agent/graph.py` - the same flow as a LangGraph `StateGraph`; `human_approval` pauses the graph with `interrupt()` and resumes with `Command(resume={"approved": True})`
- `scripts/run_agent.py` - runs all sample invoices and asks you to approve the big ones (`--yes` / `--no` to auto-answer, `--graph` to use LangGraph)
- `tests/test_agent.py` - end-to-end tests over the real MCP servers with a throwaway ledger (`LEDGER_DB_PATH`)

## Results on the 7 sample invoices
| File | Decision | Why |
|---|---|---|
| 01_clean.pdf | needs_approval -> recorded | passes every check, but $1,800 is over the $1,000 approval threshold |
| 02_duplicate.pdf | flagged | INV-1001 is already paid |
| 03_unapproved_vendor.pdf | flagged | vendor V003 is not approved |
| 04_over_policy.pdf | flagged | $7,200 is over Engineering's $5,000 single-invoice limit |
| 05_over_budget.pdf | flagged | $1,500 is over Marketing's remaining $1,100 |
| 06_total_mismatch.pdf | flagged | line items add up to $690, total says $790 |
| 07_small_clean.pdf | recorded | passes every check and is under $1,000 |

## Run it (Windows, VS Code terminal)
```
.venv\Scripts\activate
pip install -r requirements-agent.txt
python scripts\make_sample_invoices.py
python -m pytest -q
python scripts\run_agent.py
python scripts\run_agent.py --graph
```
To use Azure OpenAI for the explanations, create `.env` (already git-ignored) with
`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` and `AZURE_OPENAI_API_VERSION`.
Use a personal or free-tier key, never your employer's.

Note: the plain workflow and all 19 tests were run before this was saved. `agent/graph.py` could not be run yet
(LangGraph wasn't installable where it was written), so `python scripts\run_agent.py --graph` is the first thing to try; it should print the same 7 decisions.

## Be ready to explain in an interview
- Why the LLM explains but never decides (money rules must be deterministic and auditable)
- Why there are two gates: the human approval, then `record_invoice` still re-checks vendor and duplicates
- How `interrupt()` + a checkpointer lets the graph pause for a person and resume later on the same thread
- Why the agent only reaches data through MCP tools (least privilege; the same tools work for any agent)

## Your exercises
1. Make the approval threshold different per department (add a column to the `policy` table).
2. Add an `approve` path to `run_agent.py --graph` that records who approved it, then show it in `list_pending_invoices`.
3. Commit after each exercise.

## Next: Week 5
Evaluation suite: turn the 7 samples (plus more) into a DeepEval test set, score decision accuracy and explanation faithfulness with LLM-as-judge, and trace every tool call.
