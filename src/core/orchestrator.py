"""Main orchestrator for coordinating all components."""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from src.core.config import get_settings
from src.retrieval.vector_store import get_vector_store
from src.agents.local_data_agent import LocalDataAgent
from src.agents.search_agent import SearchAgent
from src.agents.cloud_agent import CloudAgent
from src.agents.aggregator_agent import AggregatorAgent
from src.agents.snowflake_agent import SnowflakeAgent
from src.tools.calculator import get_calculator
from src.tools.web_search import get_web_search
from src.tools.database_query import get_database_query
from openai import OpenAI

logger = logging.getLogger(__name__)


class Tier(Enum):
    """System tiers."""
    BASIC_RAG = "basic"
    AGENT_WITH_TOOLS = "agent"
    ADVANCED_AGENTIC = "advanced"


class Orchestrator:
    """Main orchestrator for the RAG system."""

    def __init__(self):
        """Initialize orchestrator."""
        self.settings = get_settings()
        self.client = OpenAI(**self.settings.get_openai_client_kwargs())
        self.model = self.settings.openai_model

        # Initialize components
        self.vector_store = get_vector_store()

        # Initialize agents (lazy loading)
        self._local_agent: Optional[LocalDataAgent] = None
        self._search_agent: Optional[SearchAgent] = None
        self._cloud_agent: Optional[CloudAgent] = None
        self._snowflake_agent: Optional[SnowflakeAgent] = None
        self._aggregator_agent: Optional[AggregatorAgent] = None

        # Initialize tools
        self.calculator = get_calculator()
        self.web_search = get_web_search()
        self.database_query = get_database_query()

    async def process_query(
        self,
        query: str,
        tier: str = "basic",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a query using the specified tier.

        Args:
            query: User query
            tier: System tier ("basic", "agent", or "advanced")
            session_id: Optional session ID for memory

        Returns:
            Response dictionary
        """
        try:
            tier_enum = Tier(tier.lower())

            if tier_enum == Tier.BASIC_RAG:
                return await self._process_basic_rag(query, session_id)
            elif tier_enum == Tier.AGENT_WITH_TOOLS:
                return await self._process_agent_with_tools(query, session_id)
            elif tier_enum == Tier.ADVANCED_AGENTIC:
                return await self._process_advanced_agentic(query, session_id)
            else:
                raise ValueError(f"Unknown tier: {tier}")

        except ValueError as e:
            logger.error(f"Invalid tier: {e}")
            return {
                "success": False,
                "error": f"Invalid tier: {tier}",
            }
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _process_basic_rag(
        self,
        query: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Process query using basic RAG (retrieval + generation)."""
        try:
            # Check if OpenAI API key is configured
            if not self.settings.openai_api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
                    "tier": "basic",
                }

            # Retrieve relevant documents
            results = self.vector_store.search(query=query, n_results=5)

            # Build context - use retrieved documents if available, otherwise use empty context
            if results["documents"]:
                context_parts = ["Retrieved documents:"]
                for i, (doc, metadata) in enumerate(
                    zip(results["documents"], results["metadatas"]), 1
                ):
                    source = metadata.get("source", "Unknown")
                    context_parts.append(f"\n[{i}] Source: {source}")
                    # Ensure doc is a string
                    doc_str = str(doc) if doc else ""
                    context_parts.append(f"Content: {doc_str[:500]}...")
                context = "\n".join(context_parts)
                sources = [
                    {"id": id, "metadata": meta}
                    for id, meta in zip(results["ids"], results["metadatas"])
                ]
            else:
                context = "No relevant documents found in the knowledge base."
                sources = []

            # Generate response using LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}",
                },
            ]

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                )

                answer = response.choices[0].message.content
            except Exception as api_error:
                error_msg = str(api_error)
                if "quota" in error_msg.lower() or "429" in error_msg:
                    raise Exception("OpenAI API quota exceeded. Please check your billing and plan details.")
                elif "api key" in error_msg.lower() or "401" in error_msg:
                    raise Exception("Invalid OpenAI API key. Please check your .env file.")
                else:
                    raise Exception(f"OpenAI API error: {error_msg}")

            return {
                "success": True,
                "answer": answer,
                "tier": "basic",
                "sources": sources,
                "model": self.model,
            }

        except Exception as e:
            logger.error(f"Error in basic RAG: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing query: {str(e)}",
                "tier": "basic",
            }

    async def _process_agent_with_tools(
        self,
        query: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Process query using agent with tools."""
        try:
            # Check if OpenAI API key is configured
            if not self.settings.openai_api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
                    "tier": "agent",
                }

            # Use local agent with tools enabled
            if not self._local_agent:
                self._local_agent = LocalDataAgent(use_planning=True)

            # Add tools to agent
            self._local_agent.add_tool(
                tool=self.calculator.get_tool_schema(),
                tool_function=lambda expression: self.calculator.calculate(expression),
            )

            if self.settings.has_web_search():
                async def web_search_tool(query: str, max_results: int = 5):
                    return await self.web_search.search(query, max_results)
                
                self._local_agent.add_tool(
                    tool=self.web_search.get_tool_schema(),
                    tool_function=web_search_tool,
                )

            if self.settings.database_url:
                def db_query_tool(sql: str, limit: int = 100):
                    return self.database_query.query(sql, limit)
                
                self._local_agent.add_tool(
                    tool=self.database_query.get_tool_schema(),
                    tool_function=db_query_tool,
                )

            # Process query
            response = await self._local_agent.process(query, session_id)

            return {
                **response,
                "tier": "agent",
            }

        except Exception as e:
            logger.error(f"Error in agent with tools: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing query: {str(e)}",
                "tier": "agent",
            }

    async def _process_advanced_agentic(
        self,
        query: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Process query using advanced agentic RAG with multiple agents."""
        try:
            # Check if OpenAI API key is configured
            if not self.settings.openai_api_key:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
                    "tier": "advanced",
                }

            # Use aggregator agent
            if not self._aggregator_agent:
                self._aggregator_agent = AggregatorAgent(use_planning=True)
                
                # Add Snowflake agent if configured
                if self.settings.has_snowflake() and not self._snowflake_agent:
                    snowflake_config = self.settings.get_snowflake_config()
                    self._snowflake_agent = SnowflakeAgent(
                        snowflake_config=snowflake_config,
                        use_planning=False
                    )
                    # Note: AggregatorAgent will automatically discover SnowflakeAgent
                    # through its agent selection logic

            # Process query
            response = await self._aggregator_agent.process(query, session_id)

            return {
                **response,
                "tier": "advanced",
            }

        except Exception as e:
            logger.error(f"Error in advanced agentic: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Error processing query: {str(e)}",
                "tier": "advanced",
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {
            "tiers_available": ["basic", "agent", "advanced"],
            "agents": {},
        }

        if self._local_agent:
            status["agents"]["local"] = self._local_agent.get_status()
        if self._search_agent:
            status["agents"]["search"] = self._search_agent.get_status()
        if self._cloud_agent:
            status["agents"]["cloud"] = self._cloud_agent.get_status()
        if self._snowflake_agent:
            status["agents"]["snowflake"] = self._snowflake_agent.get_status()
        if self._aggregator_agent:
            status["agents"]["aggregator"] = self._aggregator_agent.get_status()

        return status

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "vector_store": {
                "document_count": self.vector_store.count(),
                "collection_name": self.settings.chroma_collection_name,
            },
            "tools": {
                "calculator": True,
                "web_search": self.settings.has_web_search(),
                "database": bool(self.settings.database_url),
                "snowflake": self.settings.has_snowflake(),
            },
            "memory": {
                "short_term_enabled": True,
                "long_term_enabled": self.settings.long_term_memory_enabled,
            },
            "model": self.model,
        }


# Global instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

