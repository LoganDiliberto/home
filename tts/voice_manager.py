"""Utility functions for voice management and validation."""

import os
import logging
import wave
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple

# Try to import soundfile, fallback to wave module if not available
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    sf = None

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent
RECORDINGS_DIR = BASE_DIR / "recordings"
VOICES_DIR = BASE_DIR / "voices"


def ensure_directories():
    """Ensure required directories exist."""
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    VOICES_DIR.mkdir(parents=True, exist_ok=True)


def get_recording_path(voice_name: str) -> Path:
    """Get the path to a recording file."""
    return RECORDINGS_DIR / f"{voice_name}.wav"


def get_voice_path(voice_name: str) -> Path:
    """Get the path to a cloned voice directory."""
    return VOICES_DIR / voice_name


def list_cloned_voices() -> List[str]:
    """List all available cloned voices."""
    ensure_directories()
    voices = []
    if VOICES_DIR.exists():
        for item in VOICES_DIR.iterdir():
            if item.is_dir():
                # Check if it's a valid voice directory (has required files)
                voice_file = item / "voice.wav"
                if voice_file.exists():
                    voices.append(item.name)
    return sorted(voices)


def list_recordings() -> List[str]:
    """List all available recordings."""
    ensure_directories()
    recordings = []
    if RECORDINGS_DIR.exists():
        for item in RECORDINGS_DIR.iterdir():
            if item.is_file() and item.suffix.lower() == ".wav":
                recordings.append(item.stem)
    return sorted(recordings)


def validate_recording(file_path: str) -> Tuple[bool, str]:
    """
    Validate a recording file.
    Returns (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    
    try:
        if SOUNDFILE_AVAILABLE:
            # Use soundfile for more detailed validation
            data, sample_rate = sf.read(file_path)
            
            # Check if it's mono (convert to mono if stereo)
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Calculate duration
            duration = len(data) / sample_rate
            
            # Validate duration (30-60 seconds recommended, but allow 10-120)
            if duration < 10:
                return False, f"Recording too short: {duration:.1f} seconds (minimum 10 seconds)"
            if duration > 120:
                return False, f"Recording too long: {duration:.1f} seconds (maximum 120 seconds)"
            
            # Validate sample rate (should be 16kHz or higher)
            if sample_rate < 16000:
                return False, f"Sample rate too low: {sample_rate} Hz (minimum 16000 Hz)"
            
            # Check audio quality (check for silence/too quiet)
            max_amplitude = np.max(np.abs(data))
            if max_amplitude < 0.01:
                return False, "Recording appears to be too quiet or silent"
            
            return True, f"Valid recording: {duration:.1f} seconds, {sample_rate} Hz"
        else:
            # Fallback to wave module (basic validation)
            with wave.open(file_path, 'rb') as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.getnframes()
                duration = frames / sample_rate
                
                # Basic validation
                if duration < 10:
                    return False, f"Recording too short: {duration:.1f} seconds (minimum 10 seconds)"
                if duration > 120:
                    return False, f"Recording too long: {duration:.1f} seconds (maximum 120 seconds)"
                if sample_rate < 16000:
                    return False, f"Sample rate too low: {sample_rate} Hz (minimum 16000 Hz)"
                
                return True, f"Valid recording: {duration:.1f} seconds, {sample_rate} Hz, {channels} channel(s)"
        
    except Exception as e:
        return False, f"Error reading audio file: {str(e)}"


def preprocess_audio(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Preprocess audio file: normalize, convert to mono.
    Note: Coqui TTS can handle various sample rates, so we don't resample here.
    Returns path to processed file.
    """
    if not SOUNDFILE_AVAILABLE:
        raise ImportError("soundfile is required for audio preprocessing. Install with: pip install soundfile")
    
    if output_path is None:
        output_path = file_path.replace(".wav", "_processed.wav")
    
    try:
        # Load audio
        data, sample_rate = sf.read(file_path)
        
        # Convert to mono if stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Normalize audio
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data / max_val * 0.95  # Normalize to 95% to avoid clipping
        
        # Save processed audio
        sf.write(output_path, data, sample_rate)
        logger.info(f"Preprocessed audio saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error preprocessing audio: {e}")
        raise


def get_audio_info(file_path: str) -> dict:
    """Get information about an audio file."""
    try:
        if SOUNDFILE_AVAILABLE:
            data, sample_rate = sf.read(file_path)
            duration = len(data) / sample_rate
            channels = 1 if len(data.shape) == 1 else data.shape[1]
            
            return {
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "samples": len(data),
                "format": "mono" if channels == 1 else f"stereo ({channels} channels)"
            }
        else:
            # Fallback using wave module
            with wave.open(file_path, 'rb') as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.getnframes()
                duration = frames / sample_rate
                
                return {
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "samples": frames,
                    "format": "mono" if channels == 1 else f"stereo ({channels} channels)"
                }
    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        return {}


# Initialize directories on import
ensure_directories()

