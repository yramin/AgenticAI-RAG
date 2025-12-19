"""Local data MCP server."""

import logging
from typing import Any, Dict

try:
    from mcp.types import Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create a mock Tool class for type hints
    class Tool:
        def __init__(self, **kwargs):
            pass

from src.mcp.mcp_server import BaseMCPServer
from src.retrieval.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class LocalMCPServer(BaseMCPServer):
    """MCP server for local document operations."""

    def __init__(self):
        """Initialize local MCP server."""
        super().__init__("local_data_server")
        self.vector_store = get_vector_store()
        self._register_tools()

    def _register_tools(self):
        """Register local data tools."""
        # Search documents tool
        search_tool = Tool(
            name="search_local_documents",
            description="Search local documents in the vector store",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        )
        self.register_tool(search_tool)

        # Get document by ID tool
        get_doc_tool = Tool(
            name="get_local_document",
            description="Get a document by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document ID",
                    },
                },
                "required": ["document_id"],
            },
        )
        self.register_tool(get_doc_tool)

        # List documents tool
        list_docs_tool = Tool(
            name="list_local_documents",
            description="List all documents in the vector store",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return",
                        "default": 10,
                    },
                },
            },
        )
        self.register_tool(list_docs_tool)

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a local data tool."""
        if name == "search_local_documents":
            query = arguments.get("query", "")
            n_results = arguments.get("n_results", 5)
            results = self.vector_store.search(query=query, n_results=n_results)
            return {
                "documents": results["documents"],
                "ids": results["ids"],
                "metadatas": results["metadatas"],
            }

        elif name == "get_local_document":
            document_id = arguments.get("document_id")
            results = self.vector_store.get_by_ids([document_id])
            if results["documents"]:
                return {
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                }
            else:
                return {"error": "Document not found"}

        elif name == "list_local_documents":
            limit = arguments.get("limit", 10)
            count = self.vector_store.count()
            return {
                "total_documents": count,
                "limit": limit,
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

