"""The evaluation suite itself: the agent must pass it, and the scorers must catch real mistakes."""
from evals import judge, run


def test_agent_passes_the_evaluation_suite():
    summary = run.main()
    assert summary["cases"] >= 17
    assert summary["decision_accuracy"] == 1.0
    assert summary["reason_recall"] == 1.0
    assert summary["unsafe_records"] == []
    assert summary["explanation_rule_pass_rate"] == 1.0


def test_rule_check_catches_an_invented_amount():
    result = judge.rule_check("flagged", "Flagged INV-1 for $950.00: over budget.", {900.0})
    assert result["passed"] is False and result["invented_amounts"] == [950.0]


def test_rule_check_catches_a_softened_decision():
    result = judge.rule_check("flagged", "INV-1 for $900.00 looks fine to pay.", {900.0})
    assert result["passed"] is False and result["states_decision"] is False


def test_scorer_counts_an_unsafe_record():
    row = {"id": "x", "expected": "flagged", "decision": "recorded", "tools": ["extract_invoice", "record_invoice"],
           "mentions_expected": ["not approved"], "mentions_found": [], "explanation": "Recorded x.",
           "allowed_amounts": [], "ms": 1.0}
    summary = run.score([row])
    assert summary["unsafe_records"] == ["x"] and summary["missed_flags"] == ["x"] and summary["decision_accuracy"] == 0
