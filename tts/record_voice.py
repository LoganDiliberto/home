"""Interactive script to record voice samples for cloning."""

import os
import sys
import time
import wave
import pyaudio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts.voice_manager import get_recording_path, validate_recording, ensure_directories

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050  # 22050 Hz sample rate (good for TTS)
RECORD_SECONDS = 60  # Maximum recording duration


def record_audio(duration: int = RECORD_SECONDS) -> bytes:
    """Record audio from microphone."""
    audio = pyaudio.PyAudio()
    
    print(f"\nRecording for up to {duration} seconds...")
    print("Speak naturally. Press Ctrl+C to stop early.\n")
    
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    frames = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            # Show progress
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and elapsed > 0:
                print(f"Recording... {int(elapsed)}/{duration} seconds", end='\r')
        
        print(f"\nRecording complete: {duration} seconds")
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\nRecording stopped early: {elapsed:.1f} seconds")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    return b''.join(frames)


def save_recording(audio_data: bytes, file_path: Path, sample_rate: int = RATE):
    """Save recorded audio to WAV file."""
    with wave.open(str(file_path), 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)


def main():
    """Main recording function."""
    ensure_directories()
    
    print("=" * 60)
    print("Voice Recording for Cloning")
    print("=" * 60)
    print("\nThis script will record your voice for cloning.")
    print("Recommended: 30-60 seconds of clear, natural speech.")
    print("Speak in a quiet environment with minimal background noise.\n")
    
    # Get voice name
    voice_name = input("Enter a name for this voice: ").strip()
    if not voice_name:
        print("Error: Voice name cannot be empty.")
        return
    
    # Clean voice name (remove invalid characters)
    voice_name = "".join(c for c in voice_name if c.isalnum() or c in (' ', '-', '_')).strip()
    voice_name = voice_name.replace(' ', '_')
    
    recording_path = get_recording_path(voice_name)
    
    # Check if recording already exists
    if recording_path.exists():
        response = input(f"\nRecording '{voice_name}' already exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return
    
    # Get recording duration
    try:
        duration_input = input("\nRecording duration in seconds (default 60, recommended 30-60): ").strip()
        duration = int(duration_input) if duration_input else RECORD_SECONDS
        if duration < 10:
            print("Duration too short, using minimum of 10 seconds.")
            duration = 10
        elif duration > 120:
            print("Duration too long, using maximum of 120 seconds.")
            duration = 120
    except ValueError:
        print("Invalid input, using default 60 seconds.")
        duration = RECORD_SECONDS
    
    print(f"\nReady to record. Starting in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"{i}...", end=' ', flush=True)
        time.sleep(1)
    print("GO!\n")
    
    try:
        # Record audio
        audio_data = record_audio(duration)
        
        if len(audio_data) == 0:
            print("Error: No audio recorded.")
            return
        
        # Save recording
        save_recording(audio_data, recording_path)
        print(f"\nRecording saved to: {recording_path}")
        
        # Validate recording
        is_valid, message = validate_recording(str(recording_path))
        print(f"Validation: {message}")
        
        if is_valid:
            print("\n✓ Recording is valid and ready for cloning!")
            print(f"\nNext step: Run 'python tts/clone_voice.py {voice_name}' to create the voice clone.")
        else:
            print(f"\n⚠ Warning: {message}")
            print("You may want to re-record for better results.")
        
    except Exception as e:
        print(f"\nError during recording: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRecording cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

