"""ReAct (Reasoning + Acting) planner implementation."""

import logging
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions in ReAct loop."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"


class ReActPlanner:
    """ReAct planner that implements thought-action-observation loop."""

    def __init__(
        self,
        max_iterations: int = 10,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize ReAct planner.

        Args:
            max_iterations: Maximum number of ReAct iterations
            tools: List of available tools with their schemas
        """
        self.max_iterations = max_iterations
        self.tools = tools or []
        self.tool_map = {tool["name"]: tool for tool in self.tools}

    def plan(
        self,
        query: str,
        context: Optional[str] = None,
        llm_call: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Generate a plan using ReAct methodology.

        Args:
            query: User query
            context: Optional context information
            llm_call: Function to call LLM (should return structured response)

        Returns:
            Plan dictionary with steps and reasoning
        """
        if not llm_call:
            raise ValueError("llm_call function is required")

        steps = []
        observations = []
        current_context = context or ""

        for iteration in range(self.max_iterations):
            # Build prompt for this iteration
            prompt = self._build_react_prompt(
                query=query,
                context=current_context,
                steps=steps,
                observations=observations,
            )

            # Get LLM response
            try:
                response = llm_call(prompt)
                step = self._parse_react_response(response)

                steps.append(step)

                # Check if we have a final answer
                if step["type"] == ActionType.FINAL_ANSWER:
                    return {
                        "query": query,
                        "steps": steps,
                        "final_answer": step.get("content", ""),
                        "iterations": iteration + 1,
                    }

                # Execute action if needed
                if step["type"] == ActionType.ACTION:
                    observation = self._execute_action(step)
                    observations.append(observation)
                    steps.append({
                        "type": ActionType.OBSERVATION,
                        "content": observation,
                        "iteration": iteration + 1,
                    })

            except Exception as e:
                logger.error(f"Error in ReAct iteration {iteration}: {e}")
                steps.append({
                    "type": ActionType.OBSERVATION,
                    "content": f"Error: {str(e)}",
                    "iteration": iteration + 1,
                })

        # Max iterations reached
        return {
            "query": query,
            "steps": steps,
            "final_answer": None,
            "iterations": self.max_iterations,
            "status": "max_iterations_reached",
        }

    def _build_react_prompt(
        self,
        query: str,
        context: str,
        steps: List[Dict[str, Any]],
        observations: List[str],
    ) -> str:
        """Build ReAct prompt."""
        prompt_parts = [
            "You are a helpful assistant that uses the ReAct (Reasoning + Acting) methodology.",
            "You can think, take actions using tools, and observe results.",
            "",
            "Available tools:",
        ]

        for tool in self.tools:
            prompt_parts.append(f"- {tool['name']}: {tool.get('description', '')}")
            if "parameters" in tool:
                prompt_parts.append(f"  Parameters: {tool['parameters']}")

        prompt_parts.extend([
            "",
            "Format your responses as:",
            "Thought: <your reasoning>",
            "Action: <tool_name>",
            "Action Input: <tool_parameters>",
            "Observation: <result>",
            "",
            "When you have the final answer, use:",
            "Final Answer: <your answer>",
            "",
        ])

        if context:
            prompt_parts.extend([
                f"Context: {context}",
                "",
            ])

        prompt_parts.append(f"Question: {query}")
        prompt_parts.append("")

        # Add previous steps
        if steps:
            prompt_parts.append("Previous steps:")
            for step in steps[-3:]:  # Last 3 steps for context
                if step["type"] == ActionType.THOUGHT:
                    prompt_parts.append(f"Thought: {step.get('content', '')}")
                elif step["type"] == ActionType.ACTION:
                    prompt_parts.append(f"Action: {step.get('action', '')}")
                    prompt_parts.append(f"Action Input: {step.get('input', '')}")
                elif step["type"] == ActionType.OBSERVATION:
                    prompt_parts.append(f"Observation: {step.get('content', '')}")
            prompt_parts.append("")

        prompt_parts.append("Your response:")

        return "\n".join(prompt_parts)

    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into ReAct step."""
        response = response.strip()

        # Check for final answer
        if response.startswith("Final Answer:"):
            return {
                "type": ActionType.FINAL_ANSWER,
                "content": response.replace("Final Answer:", "").strip(),
            }

        # Parse thought
        if "Thought:" in response:
            thought_part = response.split("Thought:")[1].split("Action:")[0].strip()
        else:
            thought_part = ""

        # Parse action
        action_name = None
        action_input = None

        if "Action:" in response:
            action_line = response.split("Action:")[1].split("Observation:")[0].strip()
            if "Action Input:" in action_line:
                parts = action_line.split("Action Input:")
                action_name = parts[0].strip()
                action_input = parts[1].strip()
            else:
                action_name = action_line

        if action_name:
            return {
                "type": ActionType.ACTION,
                "thought": thought_part,
                "action": action_name,
                "input": action_input or "",
            }
        else:
            return {
                "type": ActionType.THOUGHT,
                "content": thought_part or response,
            }

    def _execute_action(self, step: Dict[str, Any]) -> str:
        """Execute an action using available tools."""
        action_name = step.get("action")
        action_input = step.get("input", "")

        if action_name not in self.tool_map:
            return f"Error: Tool '{action_name}' not found"

        tool = self.tool_map[action_name]
        tool_func = tool.get("function")

        if not tool_func:
            return f"Error: Tool '{action_name}' has no implementation"

        try:
            # Parse input (assuming JSON format)
            import json
            try:
                params = json.loads(action_input) if action_input else {}
            except:
                params = {"query": action_input} if action_input else {}

            result = tool_func(**params)
            return str(result)
        except Exception as e:
            return f"Error executing {action_name}: {str(e)}"

    def add_tool(self, tool: Dict[str, Any]) -> None:
        """Add a tool to the planner."""
        self.tools.append(tool)
        self.tool_map[tool["name"]] = tool

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.tools

