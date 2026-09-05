# Copyright 2026 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Static passthrough tools for MCP clients without tools/list_changed support.

Upstream only exposes the Colab frontend tools after the browser connects,
notifying the client via notifications/tools/list_changed. Clients that do
not act on that notification (e.g. Kimi CLI) would never see the tools. This
module registers the known Colab tools statically at server startup instead.
Each tool forwards its call to the connected Colab frontend session, or
returns instructions to connect first when no session is live.

The tool definitions below were captured from the Colab frontend MCP server
with scripts/dump_tools.py (see colab_tools.json). Re-run that script and
update COLAB_TOOL_DEFINITIONS if Colab changes its tool surface.
"""

from typing import TYPE_CHECKING, Any

from fastmcp.tools.tool import FunctionTool, Tool

if TYPE_CHECKING:
    from colab_mcp.session import ColabProxyClient

NOT_CONNECTED_MESSAGE = (
    "Not connected to a Colab session. Call the "
    "'open_colab_browser_connection' tool first, connect in the browser tab "
    "it opens, and then retry this call."
)

COLAB_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "add_code_cell",
        "description": "Inserts a code type cell at the provided index and shifts existing cells. The resulting new cell id is returned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellIndex": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9007199254740991,
                    "description": "The index at which to insert the cell.",
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "r", "julia"],
                    "description": "The programming language of the new cell.",
                },
                "code": {
                    "type": "string",
                    "description": "The code content of the new cell.",
                },
            },
            "required": ["cellIndex", "language", "code"],
            "additionalProperties": False,
        },
    },
    {
        "name": "add_text_cell",
        "description": "Inserts a text type cell at the provided index and shifts existing cells. The resulting new cell id is returned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellIndex": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9007199254740991,
                    "description": "The index at which to insert the cell.",
                },
                "content": {
                    "type": "string",
                    "description": "The content of the new cell. This can include Markdown and LaTeX syntax.",
                },
            },
            "required": ["cellIndex", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "delete_cell",
        "description": "Deletes the cell with the provided cell ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellId": {
                    "type": "string",
                    "description": "The ID of the cell to delete.",
                }
            },
            "required": ["cellId"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_cells",
        "description": "Gets a range of cells as JSON from the notebook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellIndexStart": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9007199254740991,
                    "description": "The starting index for the cell range (inclusive). If not provided, this defaults to 0.",
                },
                "cellIndexEnd": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9007199254740991,
                    "description": "The end index for the cell range (inclusive). This must be greater than or equal to cellIndexStart. If not provided, this defaults to the last available cell index.",
                },
                "includeOutputs": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to include the code cell execution outputs in the response. If not provided, this defaults to false.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "move_cell",
        "description": "Moves a cell to the provided index and shifts existing cells.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellId": {
                    "type": "string",
                    "description": "The ID of the cell to move.",
                },
                "cellIndex": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 9007199254740991,
                    "description": "The index to move the cell to.",
                },
            },
            "required": ["cellId", "cellIndex"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_code_cell",
        "description": "Executes the code in the cell with the provided cell ID. The cell must be acode cell type. The output of the cell execution is returned.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellId": {
                    "type": "string",
                    "description": "The ID of the code cell to execute.",
                }
            },
            "required": ["cellId"],
            "additionalProperties": False,
        },
    },
    {
        "name": "update_cell",
        "description": "Overwrites the contents of the cell with the provided new content. The cell must already exist and is identified by its cell ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cellId": {
                    "type": "string",
                    "description": "The ID of the cell to update.",
                },
                "content": {
                    "type": "string",
                    "description": "The new content of the cell.",
                },
            },
            "required": ["cellId", "content"],
            "additionalProperties": False,
        },
    },
]


def _make_passthrough_fn(tool_name: str, proxy_client: "ColabProxyClient"):
    async def _passthrough(**kwargs: Any) -> Any:
        if not proxy_client.is_connected():
            return NOT_CONNECTED_MESSAGE
        result = await proxy_client.proxy_mcp_client.call_tool(tool_name, kwargs)
        return result.content

    return _passthrough


def build_static_tools(proxy_client: "ColabProxyClient") -> list[Tool]:
    """Build the static passthrough tools that forward to the Colab frontend."""
    return [
        FunctionTool(
            fn=_make_passthrough_fn(definition["name"], proxy_client),
            name=definition["name"],
            description=definition["description"],
            parameters=definition["inputSchema"],
        )
        for definition in COLAB_TOOL_DEFINITIONS
    ]
