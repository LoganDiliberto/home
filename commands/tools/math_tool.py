"""Math/calculator tool for the agent."""

import math
import logging
from typing import Dict, Any
from core.tool import Tool

logger = logging.getLogger(__name__)


class MathTool(Tool):
    """Tool for performing mathematical calculations."""
    
    def name(self) -> str:
        """Get the tool name."""
        return "calculate"
    
    def description(self) -> str:
        """Get the tool description."""
        return "Performs mathematical calculations. Accepts mathematical expressions as strings. Supports basic operations (+, -, *, /, **), parentheses, and common math functions like sin, cos, sqrt, log, etc."
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                }
            },
            "required": ["expression"]
        }
    
    def execute(self, **kwargs) -> str:
        """Execute the math calculation."""
        expression = kwargs.get("expression", "")
        
        if not expression:
            return "Error: No expression provided"
        
        try:
            # Create a safe evaluation environment with only math functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                # Math constants
                "pi": math.pi,
                "e": math.e,
                "tau": math.tau,
                # Math functions
                "sqrt": math.sqrt,
                "exp": math.exp,
                "log": math.log,
                "log10": math.log10,
                "log2": math.log2,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "atan2": math.atan2,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "asinh": math.asinh,
                "acosh": math.acosh,
                "atanh": math.atanh,
                "degrees": math.degrees,
                "radians": math.radians,
                "ceil": math.ceil,
                "floor": math.floor,
                "fabs": math.fabs,
                "factorial": math.factorial,
                "gcd": math.gcd,
                "lcm": math.lcm,
                "fmod": math.fmod,
                "trunc": math.trunc,
            }
            
            # Evaluate the expression
            result = eval(expression, safe_dict, {})
            
            # Format the result
            if isinstance(result, float):
                # Check if it's a whole number
                if result.is_integer():
                    return str(int(result))
                else:
                    # Round to reasonable precision
                    return str(round(result, 10))
            else:
                return str(result)
                
        except ZeroDivisionError:
            return "Error: Division by zero"
        except ValueError as e:
            return f"Error: Invalid value - {str(e)}"
        except TypeError as e:
            return f"Error: Invalid operation - {str(e)}"
        except SyntaxError as e:
            return f"Error: Invalid expression syntax - {str(e)}"
        except Exception as e:
            logger.error(f"Error in math calculation: {e}", exc_info=True)
            return f"Error calculating expression: {str(e)}"

