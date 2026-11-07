"""Run every sample invoice through the agent.

    python scripts\run_agent.py            # plain workflow, asks you to approve big invoices
    python scripts\run_agent.py --graph    # same flow through the LangGraph graph (needs langgraph)
    add --yes to auto-approve, --no to auto-reject (useful for demos and tests)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import llm, workflow  # noqa: E402
from agent.tools import Toolbox  # noqa: E402
from mcp_servers.ledger.db import init_db  # noqa: E402


def ask(invoice: dict) -> bool:
    if "--yes" in sys.argv:
        return True
    if "--no" in sys.argv:
        return False
    reply = input(f"  Approve {invoice['invoice_number']} (${invoice['total']:,.2f}, {invoice['department']})? [y/N] ")
    return reply.strip().lower() == "y"


async def run_plain(tools) -> None:
    listing = await tools.call("list_documents")
    for name in listing["documents"]:
        state = await workflow.run_checks(name, tools)
        if state.decision == "needs_approval":
            state = await workflow.record(state, tools) if ask(state.invoice) else state
            if state.decision == "needs_approval":
                state.decision = "rejected_by_human"
        elif state.decision == "ready_to_record":
            state = await workflow.record(state, tools)
        print(f"{name:28} {state.decision:18} {llm.explain(state)}")


async def run_graph(tools) -> None:
    from langgraph.types import Command

    from agent.graph import build_graph

    graph = build_graph(tools)
    listing = await tools.call("list_documents")
    for i, name in enumerate(listing["documents"]):
        config = {"configurable": {"thread_id": f"invoice-{i}"}}
        result = await graph.ainvoke({"filename": name}, config)
        if "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            result = await graph.ainvoke(Command(resume={"approved": ask(payload["invoice"]), "reviewer": "you"}), config)
        print(f"{name:28} {result['decision']:18} {result['explanation']}")


async def main() -> None:
    init_db(reset=True)  # start each demo from the seed data
    async with Toolbox() as tools:
        print("Tools:", tools.tool_names, "\n")
        await (run_graph(tools) if "--graph" in sys.argv else run_plain(tools))


if __name__ == "__main__":
    asyncio.run(main())
