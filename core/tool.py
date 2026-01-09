"""Base tool interface for agent tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Tool(ABC):
    """Abstract base class for all agent tools."""
    
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the tool.
        
        Returns:
            Tool name (used as function name in OpenAI API)
        """
        pass
    
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the tool.
        
        Returns:
            Tool description (used as function description in OpenAI API)
        """
        pass
    
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for tool parameters.
        
        Returns:
            JSON schema dictionary compatible with OpenAI function calling
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Result string to be sent back to the agent
        """
        pass
    
    def to_openai_function(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function definition format.
        
        Returns:
            Dictionary in OpenAI function calling format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": self.parameters_schema()
            }
        }

