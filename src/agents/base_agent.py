"""Base agent class with common functionality."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from src.core.config import get_settings
from src.memory.short_term_memory import ShortTermMemory
from src.memory.long_term_memory import LongTermMemory
from src.planning.react_planner import ReActPlanner
from src.planning.cot_planner import CoTPlanner

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        name: str,
        description: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        use_memory: bool = True,
        use_planning: bool = False,
        planning_type: str = "react",  # "react" or "cot"
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name
            description: Agent description
            tools: List of available tools
            use_memory: Whether to use memory
            use_planning: Whether to use planning
            planning_type: Type of planning ("react" or "cot")
        """
        self.name = name
        self.description = description
        self.settings = get_settings()

        # Initialize OpenAI client
        self.client = OpenAI(**self.settings.get_openai_client_kwargs())
        self.model = self.settings.openai_model

        # Initialize memory
        self.use_memory = use_memory
        self.short_term_memory: Optional[ShortTermMemory] = None
        self.long_term_memory: Optional[LongTermMemory] = None
        if use_memory:
            self.short_term_memory = ShortTermMemory()
            self.long_term_memory = LongTermMemory()

        # Initialize planning
        self.use_planning = use_planning
        self.planning_type = planning_type
        self.planner: Optional[ReActPlanner | CoTPlanner] = None
        if use_planning:
            if planning_type == "react":
                self.planner = ReActPlanner(tools=tools or [])
            elif planning_type == "cot":
                self.planner = CoTPlanner()
            else:
                logger.warning(f"Unknown planning type: {planning_type}")

        # Tools
        self.tools = tools or []
        self.tool_functions: Dict[str, Callable] = {}

    def add_tool(self, tool: Dict[str, Any], tool_function: Callable) -> None:
        """
        Add a tool to the agent.

        Args:
            tool: Tool schema
            tool_function: Function to execute the tool
        """
        self.tools.append(tool)
        self.tool_functions[tool["name"]] = tool_function
        if self.planner and isinstance(self.planner, ReActPlanner):
            self.planner.add_tool(tool)

    async def process(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a query using the agent.

        Args:
            query: User query
            session_id: Optional session ID for memory
            context: Optional additional context

        Returns:
            Response dictionary
        """
        try:
            # Add user message to memory
            if self.short_term_memory:
                self.short_term_memory.add_message("user", query)

            # Load long-term memory if available
            long_term_context = ""
            if self.long_term_memory and session_id:
                memories = self.long_term_memory.search_memories(query, session_id, n_results=3)
                if memories:
                    long_term_context = "\n".join([
                        m["content"] for m in memories
                    ])

            # Combine contexts
            full_context = self._build_context(context, long_term_context)

            # Use planning if enabled
            if self.use_planning and self.planner:
                response = await self._process_with_planning(query, full_context, session_id)
            else:
                response = await self._process_direct(query, full_context, session_id)

            # Add assistant response to memory
            if self.short_term_memory and "answer" in response:
                self.short_term_memory.add_message("assistant", response["answer"])

            # Store in long-term memory
            if self.long_term_memory and session_id:
                messages = self.short_term_memory.get_messages() if self.short_term_memory else []
                self.long_term_memory.store_conversation(session_id, messages)

            return response

        except Exception as e:
            logger.error(f"Error processing query in {self.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
            }

    async def _process_direct(
        self,
        query: str,
        context: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Process query directly without planning."""
        # Build messages
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": f"{self.description}\n\nContext: {context}",
            })
        else:
            messages.append({
                "role": "system",
                "content": self.description,
            })

        # Add conversation history
        if self.short_term_memory:
            history = self.short_term_memory.get_messages(format_for_llm=True)
            messages.extend(history[-5:])  # Last 5 messages
        else:
            messages.append({
                "role": "user",
                "content": query,
            })

        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )

            answer = response.choices[0].message.content

            return {
                "success": True,
                "answer": answer,
                "agent": self.name,
                "model": self.model,
            }
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                logger.error(f"OpenAI API quota exceeded: {e}")
                raise Exception("OpenAI API quota exceeded. Please check your billing and plan details.")
            elif "api key" in error_msg.lower() or "401" in error_msg:
                logger.error(f"Invalid OpenAI API key: {e}")
                raise Exception("Invalid OpenAI API key. Please check your .env file.")
            else:
                logger.error(f"Error calling LLM: {e}")
                raise

    async def _process_with_planning(
        self,
        query: str,
        context: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        """Process query using planning."""
        if not self.planner:
            return await self._process_direct(query, context, session_id)

        # Create sync LLM call function (planner expects sync)
        def llm_call(prompt: str) -> str:
            messages = [
                {"role": "system", "content": self.description},
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content

        # Generate plan (planner methods are sync)
        if isinstance(self.planner, ReActPlanner):
            plan = self.planner.plan(
                query=query,
                context=context,
                llm_call=llm_call,
            )
        else:  # CoT planner
            plan = self.planner.plan(
                query=query,
                context=context,
                llm_call=llm_call,
            )

        # Extract final answer
        if isinstance(self.planner, ReActPlanner):
            answer = plan.get("final_answer", "I couldn't find a complete answer.")
        else:
            answer = plan.get("conclusion", "I couldn't find a complete answer.")

        return {
            "success": True,
            "answer": answer,
            "agent": self.name,
            "plan": plan,
            "model": self.model,
        }

    def _build_context(
        self,
        additional_context: Optional[str],
        long_term_context: str,
    ) -> str:
        """Build full context string."""
        parts = []
        if long_term_context:
            parts.append(f"Relevant past conversations:\n{long_term_context}")
        if additional_context:
            parts.append(f"Additional context:\n{additional_context}")
        return "\n\n".join(parts)

    async def _execute_tool(
        self,
        tool_name: str,
        **kwargs,
    ) -> Any:
        """Execute a tool (supports both sync and async tools)."""
        if tool_name not in self.tool_functions:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool_func = self.tool_functions[tool_name]
        # Check if tool is async
        import asyncio
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**kwargs)
        else:
            return tool_func(**kwargs)

    @abstractmethod
    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context for the query.

        Args:
            query: User query

        Returns:
            Context string
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": [t["name"] for t in self.tools],
            "memory_enabled": self.use_memory,
            "planning_enabled": self.use_planning,
            "planning_type": self.planning_type if self.use_planning else None,
        }

