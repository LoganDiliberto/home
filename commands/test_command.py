"""Example test command to demonstrate modularity.

This file demonstrates how easy it is to add new commands without modifying
core files. To use this command, simply import it in commands/__init__.py
and register it.
"""

import logging
from typing import TYPE_CHECKING
from core.command import Command

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)


class TestCommand(Command):
    """Example test command that responds to 'test'."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command is 'test'."""
        return command == "test"
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute test command."""
        logger.info("Test command executed")
        return "Test command works! The modular architecture is functioning correctly."
    
    def get_priority(self) -> int:
        """Medium priority for test commands."""
        return 5

