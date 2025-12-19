"""Chain-of-Thought (CoT) planner implementation."""

import logging
from typing import List, Dict, Any, Optional, Callable
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class CoTPlanner:
    """Chain-of-Thought planner for multi-step reasoning."""

    def __init__(
        self,
        max_steps: int = 10,
        enable_reflection: bool = True,
    ):
        """
        Initialize CoT planner.

        Args:
            max_steps: Maximum number of reasoning steps
            enable_reflection: Whether to enable reflection on steps
        """
        self.max_steps = max_steps
        self.enable_reflection = enable_reflection

    def plan(
        self,
        query: str,
        context: Optional[str] = None,
        llm_call: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Generate a plan using Chain-of-Thought methodology.

        Args:
            query: User query
            context: Optional context information
            llm_call: Function to call LLM

        Returns:
            Plan dictionary with reasoning chain
        """
        if not llm_call:
            raise ValueError("llm_call function is required")

        reasoning_steps = []
        current_understanding = context or ""

        # Initial reasoning prompt
        prompt = self._build_initial_prompt(query, context)

        for step_num in range(self.max_steps):
            try:
                # Get LLM response
                response = llm_call(prompt)

                # Parse response
                step = self._parse_cot_response(response, step_num)
                reasoning_steps.append(step)

                # Check if we have a conclusion
                if step.get("is_conclusion", False):
                    return {
                        "query": query,
                        "reasoning_steps": reasoning_steps,
                        "conclusion": step.get("content", ""),
                        "total_steps": step_num + 1,
                    }

                # Build next step prompt
                prompt = self._build_next_step_prompt(
                    query=query,
                    context=current_understanding,
                    previous_steps=reasoning_steps,
                    current_step=step,
                )

                # Optional: Reflection step
                if self.enable_reflection and step_num > 0 and step_num % 3 == 0:
                    reflection = self._reflect_on_progress(reasoning_steps, llm_call)
                    if reflection:
                        reasoning_steps.append({
                            "step": step_num + 1,
                            "type": "reflection",
                            "content": reflection,
                        })

            except Exception as e:
                logger.error(f"Error in CoT step {step_num}: {e}")
                reasoning_steps.append({
                    "step": step_num + 1,
                    "type": "error",
                    "content": f"Error: {str(e)}",
                })

        # Max steps reached
        return {
            "query": query,
            "reasoning_steps": reasoning_steps,
            "conclusion": None,
            "total_steps": self.max_steps,
            "status": "max_steps_reached",
        }

    def _build_initial_prompt(
        self,
        query: str,
        context: Optional[str],
    ) -> str:
        """Build initial CoT prompt."""
        prompt_parts = [
            "You are a helpful assistant that uses Chain-of-Thought reasoning.",
            "Break down complex problems into smaller steps and reason through them step by step.",
            "",
            "Format your reasoning as:",
            "Step 1: <your reasoning>",
            "Step 2: <your reasoning>",
            "...",
            "Conclusion: <final answer>",
            "",
        ]

        if context:
            prompt_parts.extend([
                f"Context: {context}",
                "",
            ])

        prompt_parts.extend([
            f"Question: {query}",
            "",
            "Begin your reasoning:",
        ])

        return "\n".join(prompt_parts)

    def _build_next_step_prompt(
        self,
        query: str,
        context: str,
        previous_steps: List[Dict[str, Any]],
        current_step: Dict[str, Any],
    ) -> str:
        """Build prompt for next reasoning step."""
        prompt_parts = [
            "Continue your Chain-of-Thought reasoning.",
            "",
            f"Question: {query}",
            "",
        ]

        if context:
            prompt_parts.append(f"Context: {context}\n")

        prompt_parts.append("Previous reasoning steps:")
        for step in previous_steps[-3:]:  # Last 3 steps
            if step.get("type") != "reflection":
                prompt_parts.append(f"Step {step.get('step', '?')}: {step.get('content', '')}")

        prompt_parts.extend([
            "",
            "What is the next step in your reasoning?",
        ])

        return "\n".join(prompt_parts)

    def _parse_cot_response(
        self,
        response: str,
        step_num: int,
    ) -> Dict[str, Any]:
        """Parse CoT response into structured step."""
        response = response.strip()

        # Check for conclusion
        if "Conclusion:" in response or response.startswith("Conclusion"):
            conclusion_part = response.split("Conclusion:")[-1].strip()
            return {
                "step": step_num + 1,
                "type": "conclusion",
                "content": conclusion_part,
                "is_conclusion": True,
            }

        # Extract step number and content
        step_content = response
        step_type = "reasoning"

        # Try to extract step number
        if response.startswith(f"Step {step_num + 1}:"):
            step_content = response.split(":", 1)[1].strip()
        elif "Step" in response:
            # Extract any step number
            parts = response.split("Step", 1)
            if len(parts) > 1:
                step_part = parts[1].split(":", 1)
                if len(step_part) > 1:
                    step_content = step_part[1].strip()

        return {
            "step": step_num + 1,
            "type": step_type,
            "content": step_content,
            "is_conclusion": False,
        }

    def _reflect_on_progress(
        self,
        steps: List[Dict[str, Any]],
        llm_call: Callable,
    ) -> Optional[str]:
        """Reflect on reasoning progress."""
        if not steps:
            return None

        reflection_prompt = (
            "Review the following reasoning steps and provide a brief reflection:\n\n"
        )
        for step in steps[-3:]:
            reflection_prompt += f"Step {step.get('step', '?')}: {step.get('content', '')}\n"

        reflection_prompt += "\nReflection:"

        try:
            reflection = llm_call(reflection_prompt)
            return reflection.strip()
        except Exception as e:
            logger.error(f"Error in reflection: {e}")
            return None

    def generate_execution_plan(
        self,
        reasoning_steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate an execution plan from reasoning steps.

        Args:
            reasoning_steps: List of reasoning steps

        Returns:
            List of execution actions
        """
        execution_plan = []

        for step in reasoning_steps:
            if step.get("type") == "conclusion":
                execution_plan.append({
                    "action": "return_answer",
                    "content": step.get("content", ""),
                })
            elif step.get("type") == "reasoning":
                # Extract potential actions from reasoning
                content = step.get("content", "")
                if "search" in content.lower():
                    execution_plan.append({
                        "action": "search",
                        "reasoning": content,
                    })
                elif "calculate" in content.lower() or "compute" in content.lower():
                    execution_plan.append({
                        "action": "calculate",
                        "reasoning": content,
                    })

        return execution_plan

