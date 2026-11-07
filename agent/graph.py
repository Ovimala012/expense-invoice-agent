"""LangGraph version of the workflow, with a real human-in-the-loop pause.

    extract -> check_vendor -> check_duplicate -> check_policy -> decide
        decide --flagged--------------> explain -> END
        decide --needs_approval-------> human_approval --approved--> record -> explain -> END
                                                       --rejected--> explain -> END
        decide --ready_to_record------> record -> explain -> END

The graph pauses at human_approval with interrupt() and resumes with Command(resume=...).
Requires: pip install langgraph   (see requirements-agent.txt)
"""
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agent import llm, workflow
from agent.workflow import InvoiceState


class GraphState(TypedDict, total=False):
    filename: str
    invoice: dict
    findings: list[str]
    decision: str
    explanation: str
    reviewer: str


def _to_obj(s: GraphState) -> InvoiceState:
    return InvoiceState(filename=s["filename"], invoice=dict(s.get("invoice", {})),
                        findings=list(s.get("findings", [])), decision=s.get("decision", ""))


def _to_dict(o: InvoiceState) -> dict:
    return {"invoice": o.invoice, "findings": o.findings, "decision": o.decision}


def build_graph(tools, checkpointer=None):
    async def extract(s):
        return _to_dict(await workflow.extract(_to_obj(s), tools))

    def _check(step):
        async def node(s):
            o = _to_obj(s)
            if not o.invoice.get("complete"):  # unreadable invoice: skip the ledger checks
                return {}
            return _to_dict(await step(o, tools))
        return node

    def decide(s):
        return _to_dict(workflow.decide(_to_obj(s)))

    def human_approval(s):
        # Pauses the graph. Whatever the reviewer sends back with Command(resume=...) is returned here.
        answer = interrupt({
            "question": "Approve this invoice for payment?",
            "invoice": {k: s["invoice"].get(k) for k in ("invoice_number", "vendor_name", "department", "total")},
        })
        approved = bool(answer.get("approved")) if isinstance(answer, dict) else bool(answer)
        reviewer = answer.get("reviewer", "") if isinstance(answer, dict) else ""
        return {"decision": "approved" if approved else "rejected_by_human", "reviewer": reviewer}

    async def record(s):
        return _to_dict(await workflow.record(_to_obj(s), tools))

    def explain(s):
        return {"explanation": llm.explain(_to_obj(s))}

    g = StateGraph(GraphState)
    for name, fn in [("extract", extract), ("check_vendor", _check(workflow.check_vendor)),
                     ("check_duplicate", _check(workflow.check_duplicate)), ("check_policy", _check(workflow.check_policy)),
                     ("decide", decide), ("human_approval", human_approval), ("record", record), ("explain", explain)]:
        g.add_node(name, fn)
    g.add_edge(START, "extract")
    g.add_edge("extract", "check_vendor")
    g.add_edge("check_vendor", "check_duplicate")
    g.add_edge("check_duplicate", "check_policy")
    g.add_edge("check_policy", "decide")
    g.add_conditional_edges("decide", lambda s: s["decision"],
                            {"flagged": "explain", "needs_approval": "human_approval", "ready_to_record": "record"})
    g.add_conditional_edges("human_approval", lambda s: s["decision"],
                            {"approved": "record", "rejected_by_human": "explain"})
    g.add_edge("record", "explain")
    g.add_edge("explain", END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())
