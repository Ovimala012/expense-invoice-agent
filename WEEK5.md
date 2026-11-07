# Week 5: Evaluation suite and tracing

Goal: prove the agent is reliable with numbers, not demos. Every change to the agent can be re-scored in seconds.

## Latest results (`python -m evals.run`)
| Metric | Result |
|---|---|
| Cases | 17 |
| Decision accuracy | 100% |
| Reason recall (expected reasons the agent gave) | 100% |
| Unsafe records (money recorded that should have been blocked or approved first) | 0 |
| False flags / missed flags | 0 / 0 |
| Explanation rule checks | 100% |
| Avg tool calls per invoice | 3.9 |

## What's here
- `evals/cases.py` - 17 synthetic invoices with the expected decision and the reasons the agent must give. Beyond the original 7, it adds a missing vendor ID, an unknown vendor, a different invoice layout, amounts exactly at and just under the $1,000 approval threshold, an invoice with three problems at once, the same invoice submitted twice in one batch, a department with no policy, and a scanned PDF with no text
- `evals/make_invoices.py` - builds those PDFs into `evals/invoices`
- `evals/run.py` - runs the agent over every case against a fresh, throwaway ledger and writes:
  - `evals/results/report.md` - the scorecard and a per-case table
  - `evals/results/results.json` - every decision, finding and explanation
  - `evals/results/traces.jsonl` - every MCP tool call with arguments, result, server and time in ms
- `evals/judge.py`
  - a rule check that always runs: the explanation must state the right decision and must not mention any dollar amount that isn't on the invoice, in the findings, or the approval threshold
  - an LLM-as-judge with DeepEval `GEval` that scores each explanation for faithfulness and completeness (0-1)
- `tests/test_eval.py` - the agent must pass the suite, and the scorers must catch an invented amount, a softened decision and an unsafe record

## Run it
```
python -m evals.run
```
With the LLM judge (uses your own Azure OpenAI key or another judge model):
```
pip install -r requirements-eval.txt
deepeval set-azure-openai --openai-endpoint <url> --openai-api-key <key> --deployment-name <deployment> --openai-api-version <version>
python -m evals.run --judge
```
The judge is most useful once the explanations come from Azure OpenAI (see WEEK3.md), because then there is something real to catch.
Note: the `--judge` path could not be run where it was written (DeepEval wasn't installable), so try it first; the rest of the suite was run and passes.

## What the suite caught while it was being built
The first run scored explanations at 47%. The agent was right; the checker was comparing "$1,800.00" in the text with "1800.0" in the data. Fixing the checker (compare numbers, not strings) took it to 100%, and a test now proves it still catches a genuinely made-up amount. It also showed the explanation said "over the approval threshold" for an invoice exactly at $1,000, so the wording now says "at or above".

## Be ready to explain in an interview
- Why "unsafe records" is the headline metric for a finance agent (a wrong flag costs minutes; a wrong payment costs money)
- Why the eval set covers edge cases at the threshold and repeated submissions, not just happy paths
- Why there is a rule-based check and an LLM judge (the rule check is free and exact; the judge catches meaning, like a softened decision)
- How the traces let you see exactly which tool calls led to each decision

## Your exercises
1. Add 3 cases of your own to `evals/cases.py` (for example, a negative total or a vendor name that doesn't match the vendor ID), run the suite, and fix anything it catches.
2. Turn on Azure OpenAI explanations and run `python -m evals.run --judge`; record the scores in this file.
3. Commit after each exercise.

## Next: Week 6
Demo video, a results section in the README, and a short write-up you can link from your resume and LinkedIn.
