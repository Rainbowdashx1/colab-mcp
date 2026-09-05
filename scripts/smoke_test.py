# Smoke test for the kimi-support branch: verifies that the server exposes the
# full Colab tool list at startup WITHOUT any browser connection (this is the
# whole point of the branch), and that passthrough tools return a clear
# not-connected message instead of failing obscurely.
#
# Usage: uv run python scripts/smoke_test.py

import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

EXPECTED_TOOLS = {
    "open_colab_browser_connection",
    "add_code_cell",
    "add_text_cell",
    "delete_cell",
    "get_cells",
    "move_cell",
    "run_code_cell",
    "update_cell",
}


async def main():
    transport = StdioTransport(command="uv", args=["run", "colab-mcp"])
    async with Client(transport) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools}
        print("Tools listed at startup:", sorted(names))
        missing = EXPECTED_TOOLS - names
        if missing:
            print(f"FAIL: missing tools: {sorted(missing)}")
            sys.exit(1)

        result = await client.call_tool("get_cells", {})
        text = result.content[0].text
        print("get_cells while disconnected ->", text)
        if "open_colab_browser_connection" not in text:
            print("FAIL: expected not-connected guidance")
            sys.exit(1)

    print("OK: all tools visible at startup, passthrough handles disconnected state")


if __name__ == "__main__":
    asyncio.run(main())
