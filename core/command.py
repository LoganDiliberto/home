"""Base command interface for the voice assistant."""

from abc import ABC, abstractmethod
from typing import Optional


class Command(ABC):
    """Abstract base class for all voice assistant commands."""
    
    @abstractmethod
    def can_handle(self, command: str) -> bool:
        """
        Check if this command can handle the given command string.
        
        Args:
            command: The normalized command string (lowercase, stripped)
            
        Returns:
            True if this command can handle the given command, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """
        Execute the command.
        
        Args:
            command: The full command string
            services: Service container with dependencies
            
        Returns:
            Response string to speak to the user
        """
        pass
    
    def get_priority(self) -> int:
        """
        Get the priority of this command. Higher priority commands are checked first.
        Default priority is 0. Commands with higher priority values are matched first.
        
        Returns:
            Priority value (default: 0)
        """
        return 0

