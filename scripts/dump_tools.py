# Utility script: dumps the tool list exposed by the Colab frontend MCP server
# to colab_tools.json. Used to generate the static tool definitions for the
# kimi-support branch (Kimi CLI does not handle notifications/tools/list_changed,
# so tools must be registered statically at server startup).
#
# Usage: uv run python scripts/dump_tools.py
# A browser tab with Colab will open; connect there and the dump happens
# automatically.

import asyncio
import json
import webbrowser

from fastmcp import Client

from colab_mcp.session import ColabTransport
from colab_mcp.websocket_server import COLAB, SCRATCH_PATH, ColabWebSocketServer

OUT_FILE = "colab_tools.json"
CONNECTION_TIMEOUT = 300  # secs to wait for the user to connect in the browser


async def main():
    async with ColabWebSocketServer() as wss:
        url = f"{COLAB}{SCRATCH_PATH}#mcpProxyToken={wss.token}&mcpProxyPort={wss.port}"
        print(f"Open this URL in your browser if no tab opens:\n{url}", flush=True)
        webbrowser.open_new(url)
        print("Waiting for the Colab frontend to connect...", flush=True)
        await asyncio.wait_for(wss.connection_live.wait(), timeout=CONNECTION_TIMEOUT)
        print("Connected! Listing tools...", flush=True)
        async with Client(ColabTransport(wss)) as client:
            tools = await client.list_tools()
            data = []
            for t in tools:
                entry = {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                }
                if t.outputSchema:
                    entry["outputSchema"] = t.outputSchema
                data.append(entry)
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Dumped {len(tools)} tools to {OUT_FILE}:", flush=True)
            for t in tools:
                print(f"  - {t.name}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
