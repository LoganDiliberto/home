"""Command handlers for the voice assistant."""

from .spotify_commands import (
    PlayCommand,
    PauseCommand,
    NextTrackCommand,
    PreviousTrackCommand,
    VolumeUpCommand,
    VolumeDownCommand
)
from .system_commands import ExitCommand
from .light_commands import TurnOnLightCommand, TurnOffLightCommand
from .llm_command import LLMCommand
from .test_command import TestCommand

# Auto-register all commands when this module is imported
from core.registry import CommandRegistry

# Global registry instance
_registry = None


def get_registry() -> CommandRegistry:
    """Get or create the global command registry with all commands registered."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        
        # Register all commands
        _registry.register(ExitCommand())
        _registry.register(PlayCommand())
        _registry.register(PauseCommand())
        _registry.register(NextTrackCommand())
        _registry.register(PreviousTrackCommand())
        _registry.register(VolumeUpCommand())
        _registry.register(VolumeDownCommand())
        _registry.register(TurnOnLightCommand())
        _registry.register(TurnOffLightCommand())
        _registry.register(TestCommand())  # Example: Easy to add new commands!
        # LLM command should be last (lowest priority) as it's the fallback
        _registry.register(LLMCommand())
    
    return _registry


__all__ = [
    'PlayCommand',
    'PauseCommand',
    'NextTrackCommand',
    'PreviousTrackCommand',
    'VolumeUpCommand',
    'VolumeDownCommand',
    'ExitCommand',
    'TurnOnLightCommand',
    'TurnOffLightCommand',
    'TestCommand',
    'LLMCommand',
    'get_registry',
]

