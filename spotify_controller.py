"""
Spotify Web API controller for voice assistant
Handles authentication, device management, and playback control
"""

import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Configure logger for this module
logger = logging.getLogger(__name__)

load_dotenv()

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8000/callback"

# Required scopes for controlling playback
SCOPE = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,app-remote-control,streaming"

# Cache file for storing tokens
CACHE_FILE = ".spotify_token_cache"

_spotify_client = None

def get_spotify_client():
    """Get or create Spotify client with OAuth authentication"""
    global _spotify_client
    
    if _spotify_client is not None:
        logger.debug("Returning existing Spotify client")
        return _spotify_client
    
    logger.info("Creating new Spotify client")
    
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        logger.error("Spotify credentials not found in environment variables")
        raise ValueError("Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
    
    logger.info("Initializing Spotify OAuth")
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_FILE
    )
    
    _spotify_client = spotipy.Spotify(auth_manager=auth_manager)
    logger.info("Spotify client created successfully")
    return _spotify_client

def get_available_devices():
    """Get list of available Spotify Connect devices"""
    logger.debug("Getting available Spotify devices")
    try:
        sp = get_spotify_client()
        devices = sp.devices()
        device_list = devices.get('devices', [])
        logger.info(f"Found {len(device_list)} available device(s)")
        for device in device_list:
            logger.debug(f"Device: {device.get('name')} (ID: {device.get('id')}, Active: {device.get('is_active')})")
        return device_list
    except Exception as e:
        logger.error(f"Error getting devices: {e}", exc_info=True)
        return []

def get_active_device():
    """Get the currently active device, or first available device"""
    logger.debug("Getting active device")
    devices = get_available_devices()
    
    # Try to find an active device
    for device in devices:
        if device.get('is_active'):
            device_id = device.get('id')
            logger.info(f"Found active device: {device.get('name')} (ID: {device_id})")
            return device_id
    
    # If no active device, return first available
    if devices:
        device_id = devices[0].get('id')
        logger.info(f"No active device found, using first available: {devices[0].get('name')} (ID: {device_id})")
        return device_id
    
    logger.warning("No Spotify devices found")
    return None

def search_and_play(query, device_id=None):
    """Search for a track/playlist/album and play it"""
    logger.info(f"Searching for and playing: {query}")
    try:
        sp = get_spotify_client()
        
        # Get device if not provided
        if device_id is None:
            device_id = get_active_device()
        
        if device_id is None:
            logger.error("No Spotify devices available")
            return "No Spotify devices found. Please open Spotify on a device."
        
        logger.debug(f"Using device ID: {device_id}")
        
        # Search for track, playlist, or album
        logger.debug(f"Searching Spotify for: {query}")
        results = sp.search(q=query, type='track,playlist,album', limit=1)
        
        uri = None
        item_type = None
        item_name = None
        
        # Check tracks first
        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            uri = track['uri']
            item_type = 'track'
            item_name = f"{track['name']} by {track['artists'][0]['name']}"
            logger.info(f"Found track: {item_name}")
        
        # Check playlists
        elif results['playlists']['items']:
            playlist = results['playlists']['items'][0]
            uri = playlist['uri']
            item_type = 'playlist'
            item_name = playlist['name']
            logger.info(f"Found playlist: {item_name}")
        
        # Check albums
        elif results['albums']['items']:
            album = results['albums']['items'][0]
            uri = album['uri']
            item_type = 'album'
            item_name = album['name']
            logger.info(f"Found album: {item_name}")
        
        if uri:
            # Start playback
            logger.info(f"Starting playback of {item_type}: {item_name}")
            sp.start_playback(device_id=device_id, context_uri=uri if item_type != 'track' else None, uris=[uri] if item_type == 'track' else None)
            logger.info(f"Successfully started playback: {item_name}")
            return f"Playing {item_name}"
        else:
            logger.warning(f"Could not find any results for query: {query}")
            return f"Could not find '{query}' on Spotify"
    
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg} (HTTP {e.http_status})", exc_info=True)
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device."
        return f"Spotify error: {e.msg}"
    except Exception as e:
        logger.error(f"Error playing music: {e}", exc_info=True)
        return f"Error playing music: {str(e)}"

def play_pause():
    """Toggle play/pause on current playback"""
    logger.info("Toggling play/pause")
    try:
        sp = get_spotify_client()
        playback = sp.current_playback()
        
        if playback is None:
            logger.warning("No active playback found")
            return "No active playback found"
        
        is_playing = playback['is_playing']
        logger.debug(f"Current playback state: {'playing' if is_playing else 'paused'}")
        
        if is_playing:
            logger.info("Pausing playback")
            sp.pause_playback()
            logger.info("Playback paused successfully")
            return "Playback paused"
        else:
            logger.info("Resuming playback")
            sp.start_playback()
            logger.info("Playback resumed successfully")
            return "Playback resumed"
    
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg} (HTTP {e.http_status})", exc_info=True)
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device."
        return f"Spotify error: {e.msg}"
    except Exception as e:
        logger.error(f"Error controlling playback: {e}", exc_info=True)
        return f"Error controlling playback: {str(e)}"

def next_track():
    """Skip to next track"""
    logger.info("Skipping to next track")
    try:
        sp = get_spotify_client()
        sp.next_track()
        logger.info("Successfully skipped to next track")
        return "Skipped to next track"
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg} (HTTP {e.http_status})", exc_info=True)
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device."
        return f"Spotify error: {e.msg}"
    except Exception as e:
        logger.error(f"Error skipping track: {e}", exc_info=True)
        return f"Error skipping track: {str(e)}"

def previous_track():
    """Go to previous track"""
    logger.info("Going to previous track")
    try:
        sp = get_spotify_client()
        sp.previous_track()
        logger.info("Successfully went to previous track")
        return "Went to previous track"
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg} (HTTP {e.http_status})", exc_info=True)
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device."
        return f"Spotify error: {e.msg}"
    except Exception as e:
        logger.error(f"Error going to previous track: {e}", exc_info=True)
        return f"Error going to previous track: {str(e)}"

def set_volume(volume):
    """Set volume (0-100)"""
    logger.info(f"Setting volume to {volume}%")
    try:
        sp = get_spotify_client()
        device_id = get_active_device()
        
        if device_id is None:
            logger.error("No active device found for volume control")
            return "No active device found. Please open Spotify on a device."
        
        # Ensure volume is between 0 and 100
        original_volume = volume
        volume = max(0, min(100, volume))
        if original_volume != volume:
            logger.warning(f"Volume adjusted from {original_volume}% to {volume}% (clamped to 0-100)")
        
        logger.debug(f"Setting volume to {volume}% on device {device_id}")
        sp.volume(volume, device_id=device_id)
        logger.info(f"Successfully set volume to {volume}%")
        return f"Volume set to {volume}%"
    
    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg} (HTTP {e.http_status})", exc_info=True)
        if e.http_status == 404:
            return "No active device found. Please open Spotify on a device."
        return f"Spotify error: {e.msg}"
    except Exception as e:
        logger.error(f"Error setting volume: {e}", exc_info=True)
        return f"Error setting volume: {str(e)}"

def get_current_playback():
    """Get current playback state"""
    logger.debug("Getting current playback state")
    try:
        sp = get_spotify_client()
        playback = sp.current_playback()
        
        if playback is None:
            logger.debug("No current playback found")
            return None
        
        playback_info = {
            'is_playing': playback.get('is_playing', False),
            'item': playback.get('item', {}),
            'device': playback.get('device', {})
        }
        
        if playback_info.get('item'):
            item_name = playback_info['item'].get('name', 'Unknown')
            logger.debug(f"Current playback: {item_name} ({'playing' if playback_info['is_playing'] else 'paused'})")
        
        return playback_info
    except Exception as e:
        logger.error(f"Error getting playback state: {e}", exc_info=True)
        return None

