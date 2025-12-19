"""Base MCP server implementation."""

import logging
from typing import Any, Dict, List, Optional
import asyncio

# Try to import MCP SDK - adjust imports based on actual SDK version
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    # Fallback if MCP SDK structure is different
    MCP_AVAILABLE = False
    logger.warning("MCP SDK not available - MCP servers will not function")

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base MCP server with common functionality."""

    def __init__(self, name: str):
        """Initialize base MCP server."""
        self.name = name
        if not MCP_AVAILABLE:
            logger.warning(f"MCP SDK not available - {name} server cannot be initialized")
            self.server = None
            self.tools: List[Any] = []
            return
            
        self.server = Server(name)
        self.tools: List[Any] = []
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers."""
        if not self.server:
            return
            
        @self.server.list_tools()
        async def list_tools() -> List[Any]:
            """List available tools."""
            return self.tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
            """Call a tool by name."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool - to be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement _execute_tool")

    def register_tool(self, tool: Any):
        """Register a tool with the server."""
        self.tools.append(tool)
        logger.info(f"Registered tool: {tool.name if hasattr(tool, 'name') else 'unknown'}")

    async def run(self):
        """Run the MCP server."""
        if not self.server or not MCP_AVAILABLE:
            logger.error("Cannot run MCP server - SDK not available")
            return
            
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

