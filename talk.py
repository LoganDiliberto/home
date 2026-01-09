# Voice assistant with "homie" wake word detection
# Continuously listens for commands starting with "homie"

import time
import logging
import re
import os
import tempfile
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from pathlib import Path

# Import modular command system
from core.services import ServiceContainer
from commands import get_registry

# Try to import Coqui TTS (optional)
try:
    from TTS.api import TTS
    COQUI_TTS_AVAILABLE = True
except ImportError:
    COQUI_TTS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to DEBUG to see more detailed loop information
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize service container and command registry
services = ServiceContainer()
services.initialize()
command_registry = get_registry()

# Initialize the speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 4000  # Adjust for ambient noise
recognizer.pause_threshold = 0.8  # Pause between phrases
recognizer.dynamic_energy_threshold = True

# Wake word
WAKE_WORD = "alexa"

# Global TTS engine instances (reused for better performance)
_pyttsx3_engine = None
_coqui_tts_engine = None
_coqui_voice_name = None


class CoquiTTSEngine:
    """Coqui TTS engine wrapper for voice cloning."""
    
    def __init__(self, voice_name: str, device: str = "cpu"):
        """Initialize Coqui TTS engine with a cloned voice."""
        if not COQUI_TTS_AVAILABLE:
            raise ImportError("Coqui TTS not available. Install with: pip install TTS")
        
        self.voice_name = voice_name
        self.device = device
        
        # Get voice path
        from tts.voice_manager import get_voice_path
        voice_dir = get_voice_path(voice_name)
        voice_file = voice_dir / "voice.wav"
        
        if not voice_file.exists():
            raise FileNotFoundError(
                f"Cloned voice not found: {voice_file}\n"
                f"Run 'python tts/clone_voice.py {voice_name}' to create it."
            )
        
        logger.info(f"Initializing Coqui TTS with voice: {voice_name}")
        logger.info("(This may take a while on first run as it downloads the model)")
        
        # Initialize TTS model
        self.tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=False
        )
        
        self.voice_file = str(voice_file)
        logger.info(f"Coqui TTS engine initialized with voice: {voice_name}")
    
    def speak(self, text: str):
        """Synthesize and play speech using the cloned voice."""
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Generate speech
            self.tts.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=self.voice_file,
                language="en"
            )
            
            # Play the audio file using pyaudio
            import wave
            import pyaudio
            
            wf = wave.open(output_path, 'rb')
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Read and play audio in chunks
            chunk = 1024
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            
            try:
                os.unlink(output_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error in Coqui TTS synthesis: {e}", exc_info=True)
            raise


def get_pyttsx3_engine():
    """Get or initialize pyttsx3 engine."""
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        _pyttsx3_engine = pyttsx3.init()
        
        # Get available voices
        voices = _pyttsx3_engine.getProperty('voices')
        
        # Prefer natural-sounding voices (in order of preference)
        preferred_voice_names = [
            'Microsoft Zira',  # Natural female voice (Windows 10+)
            'Microsoft David',  # Natural male voice (Windows 10+)
            'Microsoft Mark',   # Natural male voice (Windows 10+)
            'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0',  # Zira full path
            'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0',  # David full path
        ]
        
        # Try to find a preferred voice
        voice_found = False
        for preferred_name in preferred_voice_names:
            for voice in voices:
                if preferred_name.lower() in voice.name.lower() or preferred_name.lower() in voice.id.lower():
                    _pyttsx3_engine.setProperty('voice', voice.id)
                    logger.info(f"Using pyttsx3 voice: {voice.name} ({voice.id})")
                    voice_found = True
                    break
            if voice_found:
                break
        
        if not voice_found and voices:
            # Fallback to first available voice
            _pyttsx3_engine.setProperty('voice', voices[0].id)
            logger.info(f"Using default pyttsx3 voice: {voices[0].name}")
        
        # Configure voice properties for more natural speech
        _pyttsx3_engine.setProperty('rate', 175)  # Slightly slower for more natural pace
        _pyttsx3_engine.setProperty('volume', 0.9)  # Slightly lower for more natural sound
        
        logger.info("pyttsx3 engine initialized with natural voice settings")
    
    return _pyttsx3_engine


def get_coqui_tts_engine():
    """Get or initialize Coqui TTS engine."""
    global _coqui_tts_engine, _coqui_voice_name
    
    voice_name = os.getenv("TTS_VOICE_NAME")
    if not voice_name:
        raise ValueError(
            "TTS_VOICE_NAME environment variable not set. "
            "Set it to the name of a cloned voice."
        )
    
    device = os.getenv("COQUI_DEVICE", "cpu")
    
    # Reinitialize if voice name changed
    if _coqui_tts_engine is None or _coqui_voice_name != voice_name:
        _coqui_tts_engine = CoquiTTSEngine(voice_name, device=device)
        _coqui_voice_name = voice_name
    
    return _coqui_tts_engine


def get_tts_engine():
    """Get or initialize the TTS engine based on configuration."""
    tts_engine_type = os.getenv("TTS_ENGINE", "pyttsx3").lower()
    
    if tts_engine_type == "coqui":
        if not COQUI_TTS_AVAILABLE:
            logger.warning("Coqui TTS requested but not available. Falling back to pyttsx3.")
            logger.warning("Install with: pip install TTS")
            return get_pyttsx3_engine()
        try:
            return get_coqui_tts_engine()
        except Exception as e:
            logger.error(f"Error initializing Coqui TTS: {e}")
            logger.warning("Falling back to pyttsx3.")
            return get_pyttsx3_engine()
    else:
        return get_pyttsx3_engine()

def list_available_voices():
    """List all available TTS voices (both pyttsx3 and cloned voices)."""
    print("\nAvailable TTS Voices:")
    print("=" * 80)
    
    # List pyttsx3 voices
    print("\nSystem Voices (pyttsx3):")
    print("-" * 80)
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for i, voice in enumerate(voices, 1):
            print(f"{i}. Name: {voice.name}")
            print(f"   ID: {voice.id}")
        engine.stop()
    except Exception as e:
        print(f"Error listing pyttsx3 voices: {e}")
    
    # List cloned voices
    print("\nCloned Voices (Coqui TTS):")
    print("-" * 80)
    try:
        from tts.voice_manager import list_cloned_voices
        cloned_voices = list_cloned_voices()
        if cloned_voices:
            for i, voice in enumerate(cloned_voices, 1):
                print(f"{i}. {voice}")
        else:
            print("No cloned voices found.")
            print("Run 'python tts/record_voice.py' and 'python tts/clone_voice.py' to create one.")
    except Exception as e:
        print(f"Error listing cloned voices: {e}")
    
    print()

# Define function to clean text for TTS (remove LaTeX, special formatting)
def clean_text_for_tts(text):
    """Clean text by removing LaTeX formatting and special characters that can cause TTS issues."""
    # Remove LaTeX math delimiters: \(, \), \[, \]
    text = re.sub(r'\\[()\[\]]', '', text)
    # Replace LaTeX commands like \times with readable text
    text = re.sub(r'\\times', 'times', text)
    text = re.sub(r'\\div', 'divided by', text)
    text = re.sub(r'\\pm', 'plus or minus', text)
    text = re.sub(r'\\sqrt', 'square root of', text)
    # Remove any remaining backslashes followed by letters (LaTeX commands)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Define function to speak text
def speak_text(text):
    """Speak the given text using the configured TTS engine."""
    # Clean the text before speaking to avoid TTS issues with special formatting
    cleaned_text = clean_text_for_tts(text)
    logger.debug(f"Speaking text: {cleaned_text[:50]}...")
    try:
        engine = get_tts_engine()
        tts_engine_type = os.getenv("TTS_ENGINE", "pyttsx3").lower()
        
        if tts_engine_type == "coqui" and isinstance(engine, CoquiTTSEngine):
            # Use Coqui TTS
            engine.speak(cleaned_text)
        else:
            # Use pyttsx3
            engine.say(cleaned_text)
            engine.runAndWait()
            # Note: Don't call engine.stop() as we want to reuse the engine
        
        logger.debug("Text-to-speech completed successfully")
    except Exception as e:
        logger.error(f"Error in text-to-speech: {e}", exc_info=True)
        # Don't let TTS errors stop the program - log and continue

def process_audio(audio):
    """Process audio and check for wake word
    Returns True if should exit, False otherwise
    """
    try:
        text = recognizer.recognize_google(audio).lower()
        logger.debug(f"Recognized speech: {text}")
        
        # Check if the text starts with the wake word
        if text.startswith(WAKE_WORD.lower()):
            logger.info(f"Wake word '{WAKE_WORD}' detected")
            # Extract command after wake word
            command = text[len(WAKE_WORD):].strip()
            
            if command:
                logger.info(f"Command detected: {command}")
                response = command_registry.handle(command, services)
                logger.info(f"Response: {response}")
                
                # Check if this is an exit command
                if response == "EXIT":
                    logger.info("Exit command processed, shutting down...")
                    speak_text("Goodbye!")
                    return True
                
                speak_text(response)
            else:
                logger.warning("Wake word detected but no command found")
                speak_text("Yes?")
        
        return False
        
    except sr.UnknownValueError:
        # Speech not understood, continue listening
        logger.debug("Speech not understood, continuing to listen")
        return False
    except sr.RequestError as e:
        logger.error(f"Error with speech recognition service: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error in process_audio: {e}", exc_info=True)
        return False

def main():
    """Main loop - continuously listen for wake word"""
    logger.info("=" * 50)
    logger.info("Voice Assistant Starting")
    logger.info(f"Wake word: '{WAKE_WORD}'")
    logger.info("=" * 50)
    print(f"Voice assistant started. Say '{WAKE_WORD}' followed by your command.")
    print("Listening continuously...")
    
    try:
        microphone = sr.Microphone()
        logger.info("Microphone initialized")
        
        # Adjust for ambient noise
        with microphone as source:
            logger.info("Adjusting for ambient noise...")
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Ambient noise adjustment complete")
            logger.info("Ready to listen for commands")
            print("Ready!")
        
        # Continuously listen - keep microphone source open for better reliability
        logger.info("Entering main listening loop")
        loop_iteration = 0
        with microphone as source:
            while True:
                try:
                    loop_iteration += 1
                    logger.debug(f"Loop iteration {loop_iteration}: Waiting for audio...")
                    # Listen for audio (non-blocking, short timeout to check frequently)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    logger.debug(f"Loop iteration {loop_iteration}: Audio captured, processing...")
                    should_exit = process_audio(audio)
                    if should_exit:
                        logger.info("Exit requested, shutting down...")
                        print("\nShutting down...")
                        break
                    logger.debug(f"Loop iteration {loop_iteration}: Audio processing complete, continuing loop")
                except sr.WaitTimeoutError:
                    # Timeout is expected - continue listening
                    logger.debug(f"Loop iteration {loop_iteration}: Timeout waiting for audio (expected), continuing...")
                    continue
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received, shutting down...")
                    print("\nShutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop (iteration {loop_iteration}): {e}", exc_info=True)
                    time.sleep(0.1)
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
