"""Document MCP server: lets the expense agent list invoice PDFs and extract their fields."""
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from mcp_servers.documents.extract import extract_invoice_fields, read_pdf_text

# INVOICE_DIR can be pointed elsewhere (the evaluation suite uses eval/invoices)
INVOICE_DIR = Path(os.getenv("INVOICE_DIR", Path(__file__).resolve().parents[2] / "data" / "invoices"))

mcp = MCPServer("documents")


def _safe_path(filename: str) -> Path | None:
    """Only allow PDFs inside the invoice folder, so the agent can't read other files."""
    path = (INVOICE_DIR / filename).resolve()
    if path.parent != INVOICE_DIR.resolve() or path.suffix.lower() != ".pdf" or not path.exists():
        return None
    return path


@mcp.tool()
def list_documents() -> dict:
    """List the invoice PDFs waiting to be processed."""
    files = sorted(p.name for p in INVOICE_DIR.glob("*.pdf")) if INVOICE_DIR.exists() else []
    return {"count": len(files), "documents": files}


@mcp.tool()
def extract_invoice(filename: str) -> dict:
    """Read one invoice PDF and return its fields, plus any missing fields or warnings."""
    path = _safe_path(filename)
    if path is None:
        return {"ok": False, "reason": f"'{filename}' is not an invoice PDF in data/invoices"}
    text = read_pdf_text(path)
    if not text.strip():
        return {"ok": False, "reason": "no text found (the PDF may be a scanned image)"}
    return {"ok": True, "filename": filename, **extract_invoice_fields(text)}


if __name__ == "__main__":
    mcp.run()
