"""Connects to both MCP servers and exposes their tools as plain async calls.

The agent never touches the database or the file system directly: everything goes
through the ledger and documents MCP servers.
"""
import json
import os
import sys
import time
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVERS = {
    "ledger": "mcp_servers.ledger.server",
    "documents": "mcp_servers.documents.server",
}


class Toolbox:
    """Keeps one session open per MCP server and routes each tool call to the right one."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._tool_server: dict[str, str] = {}
        self.calls: list[dict] = []  # every tool call, for tracing and evaluation

    async def __aenter__(self) -> "Toolbox":
        for name, module in SERVERS.items():
            # pass our environment through (the MCP client only forwards a few variables by default),
            # so settings like LEDGER_DB_PATH reach the servers
            params = StdioServerParameters(command=sys.executable, args=["-m", module], env=dict(os.environ))
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self._sessions[name] = session
            for tool in (await session.list_tools()).tools:
                self._tool_server[tool.name] = name
        return self

    async def __aexit__(self, *exc) -> None:
        await self._stack.aclose()

    @property
    def tool_names(self) -> list[str]:
        return sorted(self._tool_server)

    async def call(self, tool: str, **args) -> dict:
        server = self._tool_server.get(tool)
        if server is None:
            raise ValueError(f"unknown tool '{tool}'")
        start = time.perf_counter()
        result = await self._sessions[server].call_tool(tool, args)
        data = json.loads(result.content[0].text)
        self.calls.append({"tool": tool, "server": server, "args": args, "result": data,
                           "ms": round((time.perf_counter() - start) * 1000, 1)})
        return data
