"""Spotify playback tool for the agent."""

import logging
from typing import Any, Dict

from core.tool import Tool

logger = logging.getLogger(__name__)


class SpotifyTool(Tool):
    """Search Spotify and start playback on the active Connect device."""

    def name(self) -> str:
        return "play_spotify"

    def description(self) -> str:
        return (
            "Search Spotify and play the best matching track, playlist, or album on the user's "
            "Spotify Connect device. Use a short natural query (e.g. 'ocean waves ambient', "
            "'lo-fi beats', 'rain sounds'). For mood or atmosphere requests (beach, cozy evening, "
            "forest, etc.), pick a sensible search query that matches the vibe—often combine with "
            "control_lights in the same turn."
        )

    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "What to search for on Spotify: artist, song, playlist idea, or ambient "
                        "description (e.g. 'seaside ambient', 'cricket sounds night')."
                    ),
                }
            },
            "required": ["query"],
        }

    def execute(self, **kwargs: Any) -> str:
        query = (kwargs.get("query") or "").strip()
        if not query:
            return "Error: No search query provided."

        try:
            import spotify_controller
        except ImportError as e:
            logger.error("spotify_controller not available: %s", e)
            return "Error: Spotify is not configured in this environment."

        try:
            result = spotify_controller.search_and_play(query)
            return result if isinstance(result, str) else str(result)
        except ValueError as e:
            logger.warning("Spotify not configured: %s", e)
            return (
                "Spotify is not configured (missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET). "
                "Cannot play music."
            )
        except Exception as e:
            logger.error("spotify_tool execute failed: %s", e, exc_info=True)
            return f"Error playing from Spotify: {e}"
