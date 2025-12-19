"""Web search agent for online information."""

import logging
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.web_search import get_web_search

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """Agent specialized in web search and online information."""

    def __init__(self, use_planning: bool = True):
        """Initialize search agent."""
        web_search = get_web_search()
        tools = [web_search.get_tool_schema()]

        super().__init__(
            name="search_agent",
            description=(
                "You are a specialized agent for searching the web and finding "
                "online information. You can search the internet to answer questions "
                "that require current or external information."
            ),
            tools=tools,
            use_memory=True,
            use_planning=use_planning,
            planning_type="react",
        )

        # Register tool function (async wrapper)
        async def web_search_tool(query: str, max_results: int = 5):
            return await web_search.search(query, max_results)
        
        self.add_tool(
            tool=web_search.get_tool_schema(),
            tool_function=web_search_tool,
        )
        self.web_search = web_search

    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from web search.

        Args:
            query: User query

        Returns:
            Context string from web search results
        """
        try:
            # Perform web search
            search_results = await self.web_search.search(query, max_results=5)

            if not search_results.get("success") or not search_results.get("results"):
                return "No relevant information found from web search."

            # Format results
            context_parts = ["Web search results:"]
            for i, result in enumerate(search_results["results"], 1):
                title = result.get("title", "No title")
                url = result.get("url", "")
                content = result.get("content", "")[:300]  # Truncate
                context_parts.append(f"\n[{i}] {title}")
                context_parts.append(f"URL: {url}")
                context_parts.append(f"Content: {content}...")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error retrieving web context: {e}")
            return f"Error performing web search: {str(e)}"

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Process query with web search.

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context

        Returns:
            Response dictionary
        """
        # Retrieve web context
        web_context = await self.retrieve_context(query)

        # Combine with provided context
        full_context = web_context
        if context:
            full_context = f"{context}\n\n{web_context}"

        # Process using base agent (which will use planning if enabled)
        return await super().process(query, session_id, full_context)

