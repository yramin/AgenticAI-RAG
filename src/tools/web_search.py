"""Web search tool integration."""

import logging
from typing import List, Dict, Any, Optional
import httpx
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class WebSearch:
    """Web search tool using Tavily or Serper API."""

    def __init__(self):
        """Initialize web search."""
        self.settings = get_settings()
        self.tavily_api_key = self.settings.tavily_api_key
        self.serper_api_key = self.settings.serper_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> Dict[str, Any]:
        """
        Search the web for information.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth ('basic' or 'advanced')

        Returns:
            Dictionary with search results
        """
        if self.tavily_api_key:
            return await self._search_tavily(query, max_results, search_depth)
        elif self.serper_api_key:
            return await self._search_serper(query, max_results)
        else:
            return {
                "success": False,
                "error": "No web search API key configured",
                "results": [],
            }

    async def _search_tavily(
        self,
        query: str,
        max_results: int,
        search_depth: str,
    ) -> Dict[str, Any]:
        """Search using Tavily API."""
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                })

            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
            }
        except Exception as e:
            logger.error(f"Error searching with Tavily: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }

    async def _search_serper(
        self,
        query: str,
        max_results: int,
    ) -> Dict[str, Any]:
        """Search using Serper API."""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "q": query,
                "num": max_results,
            }

            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "position": item.get("position", 0),
                })

            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
            }
        except Exception as e:
            logger.error(f"Error searching with Serper: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }

    def get_tool_schema(self) -> Dict[str, Any]:
        """Get tool schema for agent integration."""
        return {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global instance
_web_search: Optional[WebSearch] = None


def get_web_search() -> WebSearch:
    """Get or create the global web search instance."""
    global _web_search
    if _web_search is None:
        _web_search = WebSearch()
    return _web_search

