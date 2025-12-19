"""Local data agent for document queries."""

import logging
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.retrieval.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class LocalDataAgent(BaseAgent):
    """Agent specialized in querying local documents and data."""

    def __init__(self, use_planning: bool = False):
        """Initialize local data agent."""
        super().__init__(
            name="local_data_agent",
            description=(
                "You are a specialized agent for querying local documents and data. "
                "You have access to a vector store of local documents and can retrieve "
                "relevant information to answer questions."
            ),
            use_memory=True,
            use_planning=use_planning,
        )
        self.vector_store = get_vector_store()

    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from local documents.

        Args:
            query: User query

        Returns:
            Context string from retrieved documents
        """
        try:
            # Search vector store
            results = self.vector_store.search(query=query, n_results=5)

            if not results["documents"]:
                return "No relevant documents found in local data."

            # Format results
            context_parts = ["Relevant documents from local data:"]
            for i, (doc, metadata) in enumerate(
                zip(results["documents"], results["metadatas"]), 1
            ):
                source = metadata.get("source", "Unknown")
                context_parts.append(f"\n[{i}] Source: {source}")
                context_parts.append(f"Content: {doc[:500]}...")  # Truncate long docs

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Error retrieving local context: {e}")
            return f"Error retrieving local documents: {str(e)}"

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Process query with local document retrieval.

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context

        Returns:
            Response dictionary
        """
        # Retrieve local context
        local_context = await self.retrieve_context(query)

        # Combine with provided context
        full_context = local_context
        if context:
            full_context = f"{context}\n\n{local_context}"

        # Process using base agent
        return await super().process(query, session_id, full_context)

