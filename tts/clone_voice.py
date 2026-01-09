"""Script to clone a voice using Coqui TTS XTTS v2 model."""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts.voice_manager import (
    get_recording_path,
    get_voice_path,
    validate_recording,
    list_recordings,
    ensure_directories
)

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Error: TTS library not installed. Run: pip install TTS")


def clone_voice(voice_name: str, device: str = "cpu"):
    """Clone a voice from a recording using Coqui TTS XTTS v2."""
    if not TTS_AVAILABLE:
        print("TTS library is not available. Please install it first.")
        return False
    
    ensure_directories()
    
    # Get recording path
    recording_path = get_recording_path(voice_name)
    
    if not recording_path.exists():
        print(f"Error: Recording not found: {recording_path}")
        print(f"\nAvailable recordings: {', '.join(list_recordings())}")
        print(f"\nTo record a voice, run: python tts/record_voice.py")
        return False
    
    # Validate recording
    print(f"Validating recording: {recording_path}")
    is_valid, message = validate_recording(str(recording_path))
    print(f"  {message}")
    
    if not is_valid:
        print("\nError: Recording validation failed. Please re-record.")
        return False
    
    # Get voice output directory
    voice_dir = get_voice_path(voice_name)
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if voice already exists
    voice_file = voice_dir / "voice.wav"
    if voice_file.exists():
        response = input(f"\nVoice '{voice_name}' already exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return False
    
    print(f"\nInitializing Coqui TTS XTTS v2 model...")
    print("(This may take a while on first run as it downloads the model ~1.5GB)")
    
    try:
        # Initialize TTS with XTTS v2 model
        # Model name: "tts_models/multilingual/multi-dataset/xtts_v2"
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True)
        
        print(f"\nCreating voice clone from: {recording_path}")
        print("This may take a few minutes...")
        
        # Copy the recording to the voice directory as the reference
        import shutil
        shutil.copy2(recording_path, voice_file)
        
        # Test the voice by generating a short sample
        print("\nTesting voice clone with sample text...")
        test_text = "Hello, this is a test of the cloned voice."
        test_output = voice_dir / "test_output.wav"
        
        tts.tts_to_file(
            text=test_text,
            file_path=str(test_output),
            speaker_wav=str(voice_file),
            language="en"
        )
        
        print(f"\n✓ Voice clone created successfully!")
        print(f"  Voice directory: {voice_dir}")
        print(f"  Reference audio: {voice_file}")
        print(f"  Test output: {test_output}")
        print(f"\nYou can now use this voice in talk.py by setting:")
        print(f"  TTS_ENGINE=coqui")
        print(f"  TTS_VOICE_NAME={voice_name}")
        
        return True
        
    except Exception as e:
        print(f"\nError during voice cloning: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clone a voice using Coqui TTS")
    parser.add_argument(
        "voice_name",
        nargs="?",
        help="Name of the voice to clone (must have a recording in tts/recordings/)"
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use for inference (default: cpu)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available recordings"
    )
    
    args = parser.parse_args()
    
    if args.list:
        recordings = list_recordings()
        if recordings:
            print("Available recordings:")
            for rec in recordings:
                print(f"  - {rec}")
        else:
            print("No recordings found. Run 'python tts/record_voice.py' to create one.")
        return
    
    if not args.voice_name:
        # Interactive mode
        recordings = list_recordings()
        if not recordings:
            print("No recordings found.")
            print("Run 'python tts/record_voice.py' to record a voice first.")
            return
        
        print("Available recordings:")
        for i, rec in enumerate(recordings, 1):
            print(f"  {i}. {rec}")
        
        try:
            choice = input("\nSelect a recording to clone (number or name): ").strip()
            if choice.isdigit():
                voice_name = recordings[int(choice) - 1]
            else:
                voice_name = choice
        except (ValueError, IndexError):
            print("Invalid selection.")
            return
    else:
        voice_name = args.voice_name
    
    print("=" * 60)
    print("Voice Cloning with Coqui TTS")
    print("=" * 60)
    
    success = clone_voice(voice_name, device=args.device)
    
    if success:
        print("\n✓ Voice cloning completed successfully!")
    else:
        print("\n✗ Voice cloning failed.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCloning cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

