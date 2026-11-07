"""Runs the agent on every evaluation case and writes a report.

    python -m evals.run            # decision accuracy, safety, extraction, explanation rule checks, traces
    python -m evals.run --judge    # also score explanations with DeepEval LLM-as-judge (see evals/judge.py)

Writes evals/results/report.md, results.json and traces.jsonl.
"""
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals import judge  # noqa: E402
from evals.cases import CASES  # noqa: E402
from evals.make_invoices import OUT as INVOICE_DIR, make_all  # noqa: E402

RESULTS = ROOT / "evals" / "results"


async def run_all() -> list[dict]:
    # imported after the env vars are set, so the MCP servers use the eval invoices and a throwaway ledger
    from agent import llm, workflow
    from agent.tools import Toolbox

    rows = []
    async with Toolbox() as tools:
        for case in CASES:
            name = f"{case['id']}.pdf"
            first_call = len(tools.calls)
            start = time.perf_counter()
            state = await workflow.run_checks(name, tools)
            if state.decision == "ready_to_record":
                state = await workflow.record(state, tools)
            # needs_approval stops here: in the eval nobody approves, which is the safe default
            explanation = llm.explain(state)
            calls = tools.calls[first_call:]
            inv = state.invoice
            rows.append({
                "id": case["id"], "expected": case["expect"], "decision": state.decision,
                "findings": state.findings, "explanation": explanation,
                "mentions_expected": case["mentions"],
                "mentions_found": [m for m in case["mentions"] if any(m in f for f in state.findings)],
                "tools": [c["tool"] for c in calls], "trace": calls,
                "ms": round((time.perf_counter() - start) * 1000, 1),
                "extracted": {k: inv.get(k) for k in ("invoice_number", "vendor_id", "department", "total")},
                "allowed_amounts": sorted(judge.known_amounts(inv, state.findings, (workflow.APPROVAL_THRESHOLD,))),
                "invoice_summary": json.dumps({k: inv.get(k) for k in ("invoice_number", "vendor_name", "department", "total")}),
            })
    return rows


def score(rows: list[dict]) -> dict:
    n = len(rows)
    correct = [r for r in rows if r["decision"] == r["expected"]]
    wanted = sum(len(r["mentions_expected"]) for r in rows)
    found = sum(len(r["mentions_found"]) for r in rows)
    should_block = [r for r in rows if r["expected"] in ("flagged", "needs_approval")]
    # the one number that must always be zero: money recorded when it should have been blocked or approved first
    unsafe = [r["id"] for r in should_block if "record_invoice" in r["tools"] and r["decision"] == "recorded"]
    false_flags = [r["id"] for r in rows if r["expected"] != "flagged" and r["decision"] == "flagged"]
    missed_flags = [r["id"] for r in rows if r["expected"] == "flagged" and r["decision"] != "flagged"]
    for r in rows:
        r["rule_check"] = judge.rule_check(r["decision"], r["explanation"], set(r["allowed_amounts"]))
    return {
        "cases": n,
        "decision_accuracy": round(len(correct) / n, 3),
        "reason_recall": round(found / wanted, 3) if wanted else 1.0,
        "unsafe_records": unsafe,
        "false_flags": false_flags,
        "missed_flags": missed_flags,
        "explanation_rule_pass_rate": round(sum(r["rule_check"]["passed"] for r in rows) / n, 3),
        "avg_tool_calls": round(sum(len(r["tools"]) for r in rows) / n, 1),
        "avg_ms_per_invoice": round(sum(r["ms"] for r in rows) / n, 1),
    }


def write_report(summary: dict, rows: list[dict], judged: list[dict] | None) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    lines = ["# Evaluation report", "",
             f"Cases: **{summary['cases']}**  ",
             f"Decision accuracy: **{summary['decision_accuracy']:.0%}**  ",
             f"Reason recall (expected reasons the agent gave): **{summary['reason_recall']:.0%}**  ",
             f"Unsafe records (must be 0): **{len(summary['unsafe_records'])}**  ",
             f"False flags: {len(summary['false_flags'])} · Missed flags: {len(summary['missed_flags'])}  ",
             f"Explanation rule checks passed: **{summary['explanation_rule_pass_rate']:.0%}**  ",
             f"Avg tool calls per invoice: {summary['avg_tool_calls']} · Avg time per invoice: {summary['avg_ms_per_invoice']} ms",
             ""]
    if judged:
        avg = sum(j["score"] for j in judged) / len(judged)
        lines += [f"LLM-as-judge (DeepEval GEval) explanation faithfulness: **{avg:.2f}** average, "
                  f"{sum(j['passed'] for j in judged)}/{len(judged)} passed", ""]
    lines += ["| Case | Expected | Got | OK | Reasons found | Tools called |", "|---|---|---|---|---|---|"]
    for r in rows:
        ok = "yes" if r["decision"] == r["expected"] else "**NO**"
        reasons = f"{len(r['mentions_found'])}/{len(r['mentions_expected'])}" if r["mentions_expected"] else "-"
        lines.append(f"| {r['id']} | {r['expected']} | {r['decision']} | {ok} | {reasons} | {len(r['tools'])} |")
    report = RESULTS / "report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (RESULTS / "results.json").write_text(json.dumps({"summary": summary, "judge": judged, "cases": [
        {k: v for k, v in r.items() if k != "trace"} for r in rows]}, indent=2), encoding="utf-8")
    with open(RESULTS / "traces.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            for call in r["trace"]:
                f.write(json.dumps({"case": r["id"], **call}) + "\n")
    return report


def main(use_judge: bool = False) -> dict:
    from mcp_servers.ledger import db

    make_all()
    saved_env = {k: os.environ.get(k) for k in ("INVOICE_DIR", "LEDGER_DB_PATH")}
    saved_db = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["INVOICE_DIR"] = str(INVOICE_DIR)
            os.environ["LEDGER_DB_PATH"] = str(Path(tmp) / "ledger.db")
            db.DB_PATH = Path(os.environ["LEDGER_DB_PATH"])
            db.init_db()
            rows = asyncio.run(run_all())
    finally:  # leave the environment as we found it (matters when this runs inside pytest)
        db.DB_PATH = saved_db
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    summary = score(rows)
    judged = judge.llm_judge(rows) if use_judge else None
    report = write_report(summary, rows, judged)
    print(report.read_text(encoding="utf-8"))
    return summary


if __name__ == "__main__":
    main(use_judge="--judge" in sys.argv)
