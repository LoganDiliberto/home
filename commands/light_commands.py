"""Light control command handlers."""

import logging
from typing import TYPE_CHECKING
from core.command import Command

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)


class TurnOnLightCommand(Command):
    """Command to turn on lights."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn on' and 'light'."""
        return "turn on" in command and "light" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute turn on light command."""
        logger.info("Light control command detected: turn on")
        # TODO: Implement light control
        return "Turning lights on"
    
    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5


class TurnOffLightCommand(Command):
    """Command to turn off lights."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn off' and 'light'."""
        return "turn off" in command and "light" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute turn off light command."""
        logger.info("Light control command detected: turn off")
        # TODO: Implement light control
        return "Turning lights off"
    
    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5

