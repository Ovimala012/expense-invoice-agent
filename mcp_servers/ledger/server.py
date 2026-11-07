"""Ledger MCP server: tools the expense agent uses to check invoices against the books."""
from mcp.server.mcpserver import MCPServer

from mcp_servers.ledger.db import connect, init_db

mcp = MCPServer("ledger")


@mcp.tool()
def get_vendor(vendor_id: str) -> dict:
    """Look up a vendor and whether it is approved for payment."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,)).fetchone()
    if row is None:
        return {"found": False, "vendor_id": vendor_id}
    return {"found": True, "vendor_id": row["vendor_id"], "name": row["name"], "approved": bool(row["approved"])}


@mcp.tool()
def get_budget(department: str) -> dict:
    """Return a department's monthly limit, amount spent and remaining budget."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM budgets WHERE department = ?", (department,)).fetchone()
    if row is None:
        return {"found": False, "department": department}
    return {
        "found": True,
        "department": row["department"],
        "monthly_limit": row["monthly_limit"],
        "spent": row["spent"],
        "remaining": round(row["monthly_limit"] - row["spent"], 2),
    }


@mcp.tool()
def check_duplicate_invoice(vendor_id: str, invoice_number: str) -> dict:
    """Check whether this vendor's invoice number is already in the ledger."""
    with connect() as conn:
        row = conn.execute(
            "SELECT status, amount FROM invoices WHERE vendor_id = ? AND invoice_number = ?",
            (vendor_id, invoice_number),
        ).fetchone()
    if row is None:
        return {"duplicate": False}
    return {"duplicate": True, "existing_status": row["status"], "existing_amount": row["amount"]}


@mcp.tool()
def list_pending_invoices(department: str) -> dict:
    """List a department's invoices that are still waiting for human approval."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT invoice_number, vendor_id, amount FROM invoices WHERE department = ? AND status = 'pending'"
            " ORDER BY invoice_number",
            (department,),
        ).fetchall()
    invoices = [dict(r) for r in rows]
    return {"department": department, "count": len(invoices), "invoices": invoices}


@mcp.tool()
def check_policy(department: str, amount: float) -> dict:
    """Check an amount against the department's single-invoice limit and remaining budget."""
    with connect() as conn:
        row = conn.execute("SELECT max_single_invoice FROM policy WHERE department = ?", (department,)).fetchone()
    if row is None:
        return {"allowed": False, "reasons": [f"no spending policy for department '{department}'"]}
    reasons = []
    if amount > row["max_single_invoice"]:
        reasons.append(f"amount {amount:.2f} is over the single-invoice limit of {row['max_single_invoice']:.2f}")
    budget = get_budget(department)
    if budget["found"] and amount > budget["remaining"]:
        reasons.append(f"amount {amount:.2f} is over the remaining budget of {budget['remaining']:.2f}")
    return {"allowed": not reasons, "max_single_invoice": row["max_single_invoice"], "reasons": reasons}


@mcp.tool()
def record_invoice(vendor_id: str, invoice_number: str, department: str, amount: float) -> dict:
    """Record a new invoice as 'pending' (never paid automatically; a human approves payment later)."""
    if amount <= 0:
        return {"recorded": False, "reason": "amount must be positive"}
    vendor = get_vendor(vendor_id)
    if not vendor["found"]:
        return {"recorded": False, "reason": "unknown vendor"}
    if not vendor["approved"]:
        return {"recorded": False, "reason": "vendor is not approved for payment"}
    if check_duplicate_invoice(vendor_id, invoice_number)["duplicate"]:
        return {"recorded": False, "reason": "duplicate invoice"}
    with connect() as conn:
        conn.execute(
            "INSERT INTO invoices VALUES (?, ?, ?, ?, 'pending')",
            (invoice_number, vendor_id, department, amount),
        )
    return {"recorded": True, "status": "pending"}


if __name__ == "__main__":
    init_db()
    mcp.run()
