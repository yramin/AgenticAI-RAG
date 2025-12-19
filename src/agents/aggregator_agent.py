"""Aggregator agent that coordinates multiple specialized agents."""

import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.agents.base_agent import BaseAgent
from src.agents.local_data_agent import LocalDataAgent
from src.agents.search_agent import SearchAgent
from src.agents.cloud_agent import CloudAgent
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class AggregatorAgent(BaseAgent):
    """Agent that coordinates multiple specialized agents and aggregates responses."""

    def __init__(self, use_planning: bool = True):
        """Initialize aggregator agent."""
        super().__init__(
            name="aggregator_agent",
            description=(
                "You are an aggregator agent that coordinates multiple specialized agents "
                "to answer complex questions. You route queries to appropriate agents and "
                "synthesize their responses into a comprehensive answer."
            ),
            use_memory=True,
            use_planning=use_planning,
            planning_type="cot",
        )

        # Initialize specialized agents
        self.local_agent = LocalDataAgent(use_planning=False)
        self.search_agent = SearchAgent(use_planning=True)
        self.cloud_agent = CloudAgent(use_planning=False)
        
        # Initialize Snowflake agent if configured
        self.snowflake_agent = None
        from src.core.config import get_settings
        settings = get_settings()
        if settings.has_snowflake():
            from src.agents.snowflake_agent import SnowflakeAgent
            snowflake_config = settings.get_snowflake_config()
            self.snowflake_agent = SnowflakeAgent(
                snowflake_config=snowflake_config,
                use_planning=False
            )

        self.agents = {
            "local": self.local_agent,
            "search": self.search_agent,
            "cloud": self.cloud_agent,
        }
        
        if self.snowflake_agent:
            self.agents["snowflake"] = self.snowflake_agent

    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve context by querying relevant agents.

        Args:
            query: User query

        Returns:
            Aggregated context string
        """
        # Determine which agents to query based on query content
        agents_to_query = self._select_agents(query)

        # Query selected agents in parallel
        results = {}
        for agent_name, agent in agents_to_query.items():
            try:
                context = await agent.retrieve_context(query)
                results[agent_name] = context
            except Exception as e:
                logger.error(f"Error querying {agent_name} agent: {e}")
                results[agent_name] = f"Error: {str(e)}"

        # Combine results
        context_parts = ["Context from specialized agents:"]
        for agent_name, context in results.items():
            context_parts.append(f"\n--- {agent_name.upper()} AGENT ---")
            context_parts.append(context)

        return "\n".join(context_parts)

    def _select_agents(self, query: str) -> Dict[str, BaseAgent]:
        """
        Select which agents to query based on the query content.

        Args:
            query: User query

        Returns:
            Dictionary of agent names to agents
        """
        query_lower = query.lower()
        selected = {}

        # Always include local agent for document queries
        if any(keyword in query_lower for keyword in ["document", "file", "local", "data"]):
            selected["local"] = self.local_agent

        # Include search agent for current information or web queries
        if any(keyword in query_lower for keyword in [
            "current", "latest", "recent", "news", "web", "internet", "online", "search"
        ]):
            selected["search"] = self.search_agent

        # Include cloud agent for cloud-related queries
        if any(keyword in query_lower for keyword in ["cloud", "s3", "gcs", "storage", "remote"]):
            selected["cloud"] = self.cloud_agent

        # Include Snowflake agent for database/data warehouse queries
        if self.snowflake_agent and any(keyword in query_lower for keyword in [
            "snowflake", "data warehouse", "sql", "database", "query", "table", "schema"
        ]):
            selected["snowflake"] = self.snowflake_agent

        # If no specific match, use local and search by default
        if not selected:
            selected["local"] = self.local_agent
            selected["search"] = self.search_agent

        return selected

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> dict:
        """
        Process query by coordinating multiple agents.

        Args:
            query: User query
            session_id: Optional session ID
            context: Optional additional context

        Returns:
            Aggregated response dictionary
        """
        # Select agents to query
        agents_to_query = self._select_agents(query)

        # Get responses from selected agents
        agent_responses = {}
        for agent_name, agent in agents_to_query.items():
            try:
                response = await agent.process(query, session_id, context)
                agent_responses[agent_name] = response
            except Exception as e:
                logger.error(f"Error processing with {agent_name} agent: {e}")
                agent_responses[agent_name] = {
                    "success": False,
                    "error": str(e),
                }

        # Synthesize responses
        synthesized_response = await self._synthesize_responses(
            query=query,
            agent_responses=agent_responses,
            session_id=session_id,
        )

        return synthesized_response

    async def _synthesize_responses(
        self,
        query: str,
        agent_responses: Dict[str, dict],
        session_id: Optional[str],
    ) -> dict:
        """
        Synthesize responses from multiple agents.

        Args:
            query: Original query
            agent_responses: Dictionary of agent responses
            session_id: Optional session ID

        Returns:
            Synthesized response
        """
        # Collect successful responses
        successful_responses = {
            name: resp for name, resp in agent_responses.items()
            if resp.get("success", False)
        }

        if not successful_responses:
            # If no successful responses, try to return the first response with error details
            error_messages = []
            for name, resp in agent_responses.items():
                error_msg = resp.get("error", "Unknown error")
                error_messages.append(f"{name}: {error_msg}")
            
            return {
                "success": False,
                "error": f"No agents provided successful responses. Errors: {'; '.join(error_messages)}",
                "agent_responses": agent_responses,
            }

        # If only one agent responded, return its response
        if len(successful_responses) == 1:
            response = list(successful_responses.values())[0]
            response["aggregated_by"] = "single_agent"
            return response

        # Multiple responses - synthesize using LLM
        try:
            # Build synthesis prompt
            synthesis_parts = [
                "You are synthesizing responses from multiple specialized agents.",
                f"Original question: {query}",
                "",
                "Agent responses:",
            ]

            for agent_name, response in successful_responses.items():
                answer = response.get("answer", "No answer provided")
                synthesis_parts.append(f"\n{agent_name.upper()} Agent:")
                synthesis_parts.append(answer)

            synthesis_parts.extend([
                "",
                "Synthesize these responses into a comprehensive, coherent answer.",
                "If there are conflicts, note them. If information is complementary, combine it.",
            ])

            synthesis_prompt = "\n".join(synthesis_parts)

            # Call LLM for synthesis
            messages = [
                {"role": "system", "content": self.description},
                {"role": "user", "content": synthesis_prompt},
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )

            synthesized_answer = response.choices[0].message.content

            return {
                "success": True,
                "answer": synthesized_answer,
                "agent": self.name,
                "aggregated_by": "multiple_agents",
                "source_agents": list(successful_responses.keys()),
                "agent_responses": successful_responses,
                "model": self.model,
            }

        except Exception as e:
            logger.error(f"Error synthesizing responses: {e}")
            # Fallback: return first successful response
            first_response = list(successful_responses.values())[0]
            first_response["aggregated_by"] = "fallback"
            return first_response

