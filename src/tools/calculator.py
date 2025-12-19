"""Calculator tool for mathematical operations."""

import logging
import math
import operator
from typing import Any, Dict
import re

logger = logging.getLogger(__name__)


class Calculator:
    """Safe calculator for mathematical expressions."""

    # Allowed operations
    ALLOWED_OPERATORS = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "//": operator.floordiv,
        "%": operator.mod,
        "**": operator.pow,
        "^": operator.pow,
    }

    # Allowed functions
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pow": pow,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    # Allowed constants
    ALLOWED_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
    }

    def __init__(self):
        """Initialize calculator."""
        pass

    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Mathematical expression as string

        Returns:
            Dictionary with result or error
        """
        try:
            # Clean expression - ensure it's a string
            if not isinstance(expression, str):
                expression = str(expression)
            expression = expression.strip()

            # Replace constants
            for const_name, const_value in self.ALLOWED_CONSTANTS.items():
                expression = re.sub(
                    rf"\b{const_name}\b",
                    str(const_value),
                    expression,
                    flags=re.IGNORECASE,
                )

            # Replace function names
            for func_name in self.ALLOWED_FUNCTIONS.keys():
                expression = re.sub(
                    rf"\b{func_name}\b",
                    func_name,
                    expression,
                    flags=re.IGNORECASE,
                )

            # Replace ^ with ** for power
            expression = expression.replace("^", "**")

            # Build safe evaluation environment
            safe_dict = {
                "__builtins__": {},
                **self.ALLOWED_FUNCTIONS,
                **self.ALLOWED_CONSTANTS,
            }

            # Evaluate expression
            result = eval(expression, safe_dict)

            return {
                "success": True,
                "result": result,
                "expression": expression,
            }
        except ZeroDivisionError:
            return {
                "success": False,
                "error": "Division by zero",
                "expression": expression,
            }
        except Exception as e:
            logger.error(f"Error calculating expression '{expression}': {e}")
            return {
                "success": False,
                "error": str(e),
                "expression": expression,
            }

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        return base ** exponent

    def sqrt(self, value: float) -> float:
        """Calculate square root."""
        if value < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(value)

    def get_tool_schema(self) -> Dict[str, Any]:
        """Get tool schema for agent integration."""
        return {
            "name": "calculator",
            "description": "Perform mathematical calculations and evaluate expressions",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'pi * 2')",
                    },
                },
                "required": ["expression"],
            },
        }


# Global instance
_calculator: Calculator = None


def get_calculator() -> Calculator:
    """Get or create the global calculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = Calculator()
    return _calculator

