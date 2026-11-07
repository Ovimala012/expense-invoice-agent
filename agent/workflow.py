"""The invoice workflow as small, testable steps.

Every decision about money is made here in code, not by the LLM:
extract -> check vendor -> check duplicate -> check policy -> decide.
The LLM (see agent/llm.py) only writes the plain-English explanation.
"""
from dataclasses import dataclass, field

# Invoices at or above this amount need a person to approve them, even if every check passes.
APPROVAL_THRESHOLD = 1000.00


@dataclass
class InvoiceState:
    filename: str
    invoice: dict = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)  # problems that block the invoice
    decision: str = ""  # "flagged" | "needs_approval" | "recorded" | "rejected_by_human"
    explanation: str = ""


async def extract(state: InvoiceState, tools) -> InvoiceState:
    result = await tools.call("extract_invoice", filename=state.filename)
    if not result.get("ok"):
        state.findings.append(result.get("reason", "could not read the invoice"))
        return state
    state.invoice = result
    for name in result["missing_fields"]:
        state.findings.append(f"missing field: {name}")
    state.findings.extend(result["warnings"])
    return state


async def check_vendor(state: InvoiceState, tools) -> InvoiceState:
    vendor = await tools.call("get_vendor", vendor_id=state.invoice["vendor_id"])
    if not vendor["found"]:
        state.findings.append(f"vendor {state.invoice['vendor_id']} is not in the ledger")
    elif not vendor["approved"]:
        state.findings.append(f"vendor {vendor['vendor_id']} ({vendor['name']}) is not approved for payment")
    return state


async def check_duplicate(state: InvoiceState, tools) -> InvoiceState:
    inv = state.invoice
    dup = await tools.call("check_duplicate_invoice", vendor_id=inv["vendor_id"], invoice_number=inv["invoice_number"])
    if dup["duplicate"]:
        state.findings.append(
            f"invoice {inv['invoice_number']} is already in the ledger ({dup['existing_status']}, ${dup['existing_amount']:,.2f})"
        )
    return state


async def check_policy(state: InvoiceState, tools) -> InvoiceState:
    policy = await tools.call("check_policy", department=state.invoice["department"], amount=state.invoice["total"])
    state.findings.extend(policy["reasons"])
    return state


def decide(state: InvoiceState) -> InvoiceState:
    if state.findings:
        state.decision = "flagged"
    elif state.invoice["total"] >= APPROVAL_THRESHOLD:
        state.decision = "needs_approval"
    else:
        state.decision = "ready_to_record"
    return state


async def record(state: InvoiceState, tools) -> InvoiceState:
    """Save the invoice as pending. Only called when checks passed and, if needed, a human approved."""
    inv = state.invoice
    result = await tools.call(
        "record_invoice", vendor_id=inv["vendor_id"], invoice_number=inv["invoice_number"],
        department=inv["department"], amount=inv["total"],
    )
    if result["recorded"]:
        state.decision = "recorded"
    else:  # the ledger has the final say, even after approval
        state.findings.append(result["reason"])
        state.decision = "flagged"
    return state


async def run_checks(filename: str, tools) -> InvoiceState:
    """Run every check and decide. Stops early if the invoice can't be read."""
    state = await extract(InvoiceState(filename), tools)
    if state.invoice and state.invoice.get("complete"):
        for step in (check_vendor, check_duplicate, check_policy):
            state = await step(state, tools)
    return decide(state)
