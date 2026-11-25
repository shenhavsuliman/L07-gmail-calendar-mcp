"""Self-test: start the server over stdio, list its tools, call list_events(1)."""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["server.py"],
        env={**os.environ, "GOOGLE_PRIVATE_DIR": os.environ.get("GOOGLE_PRIVATE_DIR", r"C:\secrets")},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools/list ->", ", ".join(t.name for t in tools.tools))
            result = await session.call_tool("list_events", {"days_ahead": 1})
            print("tools/call list_events(days_ahead=1) ->")
            for c in result.content:
                print(" ", getattr(c, "text", c))


if __name__ == "__main__":
    asyncio.run(main())
