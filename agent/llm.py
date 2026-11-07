"""Writes the plain-English explanation for a reviewer.

Uses Azure OpenAI when these environment variables are set (put them in .env, never commit it):
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION
Otherwise it falls back to a template, so the workflow and tests run without any API key.
The LLM never changes the decision; it only explains it.
"""
import json
import os

try:  # optional: load AZURE_OPENAI_* from a local .env file
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _template(state) -> str:
    inv = state.invoice
    head = f"{inv.get('invoice_number', state.filename)} from {inv.get('vendor_name', 'unknown vendor')}"
    amount = f" for ${inv['total']:,.2f}" if "total" in inv else ""
    if state.decision == "flagged":
        return f"Flagged {head}{amount}: " + "; ".join(state.findings) + "."
    if state.decision == "needs_approval":
        return f"{head}{amount} passed all checks but needs human approval (over the approval threshold)."
    if state.decision == "recorded":
        return f"Recorded {head}{amount} as pending payment."
    if state.decision == "rejected_by_human":
        return f"{head}{amount} was rejected by the reviewer."
    return f"{head}{amount} passed all checks."


def explain(state) -> str:
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        return _template(state)
    from openai import AzureOpenAI  # imported here so the rest of the project runs without it

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    facts = {"decision": state.decision, "findings": state.findings,
             "invoice": {k: state.invoice.get(k) for k in ("invoice_number", "vendor_name", "department", "total")}}
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        temperature=0,
        messages=[
            {"role": "system", "content": "You explain accounts-payable decisions to a reviewer in 1-2 sentences. "
             "Use only the facts given. Never change or soften the decision."},
            {"role": "user", "content": json.dumps(facts)},
        ],
    )
    return response.choices[0].message.content.strip()
