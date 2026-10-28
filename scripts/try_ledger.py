"""Starts the ledger MCP server and calls its tools, the same way an agent will."""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_servers.ledger.server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            for name, args in [
                ("get_vendor", {"vendor_id": "V003"}),
                ("get_budget", {"department": "Marketing"}),
                ("check_duplicate_invoice", {"vendor_id": "V001", "invoice_number": "INV-1001"}),
                ("record_invoice", {"vendor_id": "V002", "invoice_number": "INV-2001", "department": "Engineering", "amount": 980.0}),
            ]:
                result = await session.call_tool(name, args)
                print(f"{name}({args}) -> {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
