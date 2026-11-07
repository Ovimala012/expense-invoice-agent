"""Starts the document MCP server and extracts every sample invoice, the same way an agent will."""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_servers.documents.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            listing = json.loads((await session.call_tool("list_documents", {})).content[0].text)
            for name in listing["documents"]:
                result = json.loads((await session.call_tool("extract_invoice", {"filename": name})).content[0].text)
                print(f"{name}: {result.get('invoice_number')} {result.get('vendor_id')} "
                      f"{result.get('department')} total={result.get('total')} "
                      f"missing={result.get('missing_fields')} warnings={result.get('warnings')}")
            bad = json.loads((await session.call_tool("extract_invoice", {"filename": "../ledger.db"})).content[0].text)
            print("path outside data/invoices ->", bad)


if __name__ == "__main__":
    asyncio.run(main())
