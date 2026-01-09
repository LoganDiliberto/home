"""Command registry for managing and matching voice assistant commands."""

import logging
from typing import List, Optional
from .command import Command
from .services import ServiceContainer

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry for managing voice assistant commands."""
    
    def __init__(self):
        """Initialize an empty command registry."""
        self._commands: List[Command] = []
    
    def register(self, command: Command) -> None:
        """
        Register a command with the registry.
        
        Args:
            command: Command instance to register
        """
        if command not in self._commands:
            self._commands.append(command)
            # Sort by priority (higher priority first)
            self._commands.sort(key=lambda c: c.get_priority(), reverse=True)
            logger.debug(f"Registered command: {command.__class__.__name__} (priority: {command.get_priority()})")
    
    def unregister(self, command: Command) -> None:
        """
        Unregister a command from the registry.
        
        Args:
            command: Command instance to unregister
        """
        if command in self._commands:
            self._commands.remove(command)
            logger.debug(f"Unregistered command: {command.__class__.__name__}")
    
    def find_handler(self, command: str) -> Optional[Command]:
        """
        Find a command handler for the given command string.
        Commands are checked in priority order (highest first).
        
        Args:
            command: The command string to find a handler for
            
        Returns:
            Command instance that can handle the command, or None if no handler found
        """
        command_lower = command.lower().strip()
        
        for cmd in self._commands:
            if cmd.can_handle(command_lower):
                logger.debug(f"Found handler: {cmd.__class__.__name__} for command: {command}")
                return cmd
        
        logger.debug(f"No handler found for command: {command}")
        return None
    
    def handle(self, command: str, services: ServiceContainer) -> str:
        """
        Handle a command by finding the appropriate handler and executing it.
        
        Args:
            command: The command string to handle
            services: Service container with dependencies
            
        Returns:
            Response string to speak to the user
        """
        handler = self.find_handler(command)
        
        if handler:
            try:
                return handler.execute(command, services)
            except Exception as e:
                logger.error(f"Error executing command {handler.__class__.__name__}: {e}", exc_info=True)
                return f"Error executing command: {str(e)}"
        else:
            logger.warning(f"No handler found for command: {command}")
            return "I don't understand that command."
    
    def get_all_commands(self) -> List[Command]:
        """
        Get all registered commands.
        
        Returns:
            List of all registered command instances
        """
        return self._commands.copy()

