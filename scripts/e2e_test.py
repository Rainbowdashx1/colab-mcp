# End-to-end test for the kimi-support branch: starts the server over stdio,
# opens the Colab browser connection, and exercises the static passthrough
# tools against the live Colab frontend.
#
# Usage: uv run python scripts/e2e_test.py
# A browser tab with Colab will open; connect there and the test proceeds.

import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    transport = StdioTransport(command="uv", args=["run", "colab-mcp"])
    async with Client(transport) as client:
        print("Opening Colab browser connection (connect in the tab)...", flush=True)
        result = await client.call_tool("open_colab_browser_connection", {})
        if result.content[0].text != "true":
            print("FAIL: browser connection not established")
            sys.exit(1)
        print("Connected. Adding a code cell...", flush=True)

        result = await client.call_tool(
            "add_code_cell",
            {"cellIndex": 0, "language": "python", "code": "print('hola desde kimi')"},
        )
        print("add_code_cell ->", result.content[0].text, flush=True)

        result = await client.call_tool("get_cells", {})
        print("get_cells ->", result.content[0].text[:500], flush=True)

    print("OK: end-to-end passthrough works")


if __name__ == "__main__":
    asyncio.run(main())
