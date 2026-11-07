"""Scores the reviewer-facing explanations.

1. A rule-based check that always runs (no API key needed):
   - the explanation states the right decision, and
   - every dollar amount it mentions really appears in the invoice or the findings (no made-up numbers).
2. Optional LLM-as-judge with DeepEval (GEval), when deepeval is installed and a judge model is configured,
   e.g. for Azure OpenAI:
       deepeval set-azure-openai --openai-endpoint <url> --openai-api-key <key> \
           --deployment-name <deployment> --openai-api-version <version>
   Then run: python -m evals.run --judge
"""
import re

DECISION_WORDS = {
    "flagged": ("flag",),
    "needs_approval": ("approv",),
    "recorded": ("record",),
}

_MONEY = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+\.\d{2})")


def _amounts(text: str) -> set[float]:
    return {round(float(m.replace(",", "")), 2) for m in _MONEY.findall(text)}


def known_amounts(invoice: dict, findings: list[str], extra: tuple = ()) -> set[float]:
    """Every amount the explanation is allowed to mention: the invoice's numbers, the findings' numbers, and any
    fixed values such as the approval threshold."""
    nums = {round(float(invoice["total"]), 2)} if invoice.get("total") is not None else set()
    for item in invoice.get("line_items", []):
        nums |= {round(item["unit_price"], 2), round(item["amount"], 2)}
    for f in findings:
        nums |= _amounts(f)
    return nums | {round(float(x), 2) for x in extra}


def rule_check(decision: str, explanation: str, allowed: set[float]) -> dict:
    words = DECISION_WORDS.get(decision, ())
    states_decision = any(w in explanation.lower() for w in words)
    invented = sorted(_amounts(explanation) - allowed)
    return {"states_decision": states_decision, "invented_amounts": invented,
            "passed": states_decision and not invented}


def llm_judge(cases: list[dict]) -> list[dict]:
    """GEval scores 0-1 for whether each explanation is faithful and complete. Needs deepeval + a judge model."""
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    metric = GEval(
        name="Explanation faithfulness",
        criteria=("The actual output explains an accounts-payable decision to a reviewer. Using only the context, "
                  "check that it states the same decision, mentions every finding in the context, and adds no facts, "
                  "amounts or reasons that are not in the context. Penalise any softened or changed decision."),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.CONTEXT],
        threshold=0.7,
    )
    scores = []
    for c in cases:
        test = LLMTestCase(input=f"Explain the decision for {c['id']}", actual_output=c["explanation"],
                           context=[f"decision: {c['decision']}", *[f"finding: {f}" for f in c["findings"]],
                                    f"invoice: {c['invoice_summary']}"])
        metric.measure(test)
        scores.append({"id": c["id"], "score": round(metric.score, 2), "passed": metric.is_successful(),
                       "reason": metric.reason})
    return scores
