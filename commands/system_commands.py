"""System-related command handlers."""

import logging
from typing import TYPE_CHECKING
from core.command import Command

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)


class ExitCommand(Command):
    """Command to exit the voice assistant."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command is an exit command."""
        return command in ["exit", "quit", "shutdown", "stop"]
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute exit command."""
        logger.info("Exit command detected")
        return "EXIT"
    
    def get_priority(self) -> int:
        """Very high priority for exit commands."""
        return 100

