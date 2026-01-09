"""Spotify-related command handlers."""

import logging
from typing import TYPE_CHECKING
from core.command import Command

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)


class PlayCommand(Command):
    """Command to play music on Spotify."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command starts with 'play'."""
        return command.startswith("play")
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute play command."""
        # Extract song/playlist name after "play"
        query = command[4:].strip()
        if not query:
            logger.warning("Play command received but no query specified")
            return "Please specify what to play. For example: 'play Bohemian Rhapsody'"
        
        logger.info(f"Spotify play command detected: {query}")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            result = spotify_controller.search_and_play(query)
            logger.info(f"Spotify play result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error with Spotify play command: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for play commands."""
        return 10


class PauseCommand(Command):
    """Command to pause/resume Spotify playback."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command is 'pause' or 'resume'."""
        return command in ["pause", "resume"]
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute pause/resume command."""
        logger.info(f"Spotify play/pause command detected: {command}")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            result = spotify_controller.play_pause()
            logger.info(f"Spotify play/pause result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error with Spotify play/pause: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for pause/resume commands."""
        return 10


class NextTrackCommand(Command):
    """Command to skip to next track."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command is 'next', 'next song', or 'skip'."""
        return command in ["next", "next song", "skip"]
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute next track command."""
        logger.info("Spotify next track command detected")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            result = spotify_controller.next_track()
            logger.info(f"Spotify next track result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error with Spotify next track: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for next track commands."""
        return 10


class PreviousTrackCommand(Command):
    """Command to go to previous track."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command is 'previous', 'previous song', or 'back'."""
        return command in ["previous", "previous song", "back"]
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute previous track command."""
        logger.info("Spotify previous track command detected")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            result = spotify_controller.previous_track()
            logger.info(f"Spotify previous track result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error with Spotify previous track: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for previous track commands."""
        return 10


class VolumeUpCommand(Command):
    """Command to increase volume."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'volume up'."""
        return "volume up" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute volume up command."""
        logger.info("Spotify volume up command detected")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            playback = spotify_controller.get_current_playback()
            if playback and playback.get('device'):
                current_vol = playback['device'].get('volume_percent', 50)
                new_vol = min(100, current_vol + 10)
                logger.info(f"Increasing volume from {current_vol}% to {new_vol}%")
                result = spotify_controller.set_volume(new_vol)
                logger.info(f"Spotify volume up result: {result}")
                return result
            else:
                logger.warning("No active playback found for volume control")
                return "No active playback found"
        except Exception as e:
            logger.error(f"Error with Spotify volume up: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for volume commands."""
        return 10


class VolumeDownCommand(Command):
    """Command to decrease volume."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'volume down'."""
        return "volume down" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute volume down command."""
        logger.info("Spotify volume down command detected")
        spotify_controller = services.spotify_controller
        if not spotify_controller:
            return "Spotify controller not available"
        
        try:
            playback = spotify_controller.get_current_playback()
            if playback and playback.get('device'):
                current_vol = playback['device'].get('volume_percent', 50)
                new_vol = max(0, current_vol - 10)
                logger.info(f"Decreasing volume from {current_vol}% to {new_vol}%")
                result = spotify_controller.set_volume(new_vol)
                logger.info(f"Spotify volume down result: {result}")
                return result
            else:
                logger.warning("No active playback found for volume control")
                return "No active playback found"
        except Exception as e:
            logger.error(f"Error with Spotify volume down: {e}", exc_info=True)
            return f"Error with Spotify: {str(e)}"
    
    def get_priority(self) -> int:
        """High priority for volume commands."""
        return 10

