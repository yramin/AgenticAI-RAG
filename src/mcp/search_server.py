"""Web search MCP server."""

import logging
from typing import Any, Dict

try:
    from mcp.types import Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    class Tool:
        def __init__(self, **kwargs):
            pass

from src.mcp.mcp_server import BaseMCPServer
from src.tools.web_search import get_web_search

logger = logging.getLogger(__name__)


class SearchMCPServer(BaseMCPServer):
    """MCP server for web search operations."""

    def __init__(self):
        """Initialize search MCP server."""
        super().__init__("web_search_server")
        self.web_search = get_web_search()
        self._register_tools()

    def _register_tools(self):
        """Register web search tools."""
        search_tool = Tool(
            name="web_search",
            description="Search the web for information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )
        self.register_tool(search_tool)

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a web search tool."""
        if name == "web_search":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 5)
            results = await self.web_search.search(query, max_results)
            return results
        else:
            raise ValueError(f"Unknown tool: {name}")

