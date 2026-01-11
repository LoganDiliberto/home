# Voice assistant with "homie" wake word detection
# Continuously listens for commands starting with "homie"

import time
import logging
import re
import os
import platform
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from pathlib import Path

# Import modular command system
from core.services import ServiceContainer
from commands import get_registry


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

# Global TTS engine instance (reused for better performance)
_pyttsx3_engine = None


def get_pyttsx3_engine():
    """Get or initialize pyttsx3 engine."""
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        _pyttsx3_engine = pyttsx3.init()
        
        # Get available voices
        voices = _pyttsx3_engine.getProperty('voices')
        
        # Platform-specific voice preferences
        system = platform.system()
        if system == 'Windows':
            # Windows SAPI voices
            preferred_voice_names = [
                'Microsoft Zira',  # Natural female voice (Windows 10+)
                'Microsoft David',  # Natural male voice (Windows 10+)
                'Microsoft Mark',   # Natural male voice (Windows 10+)
            ]
        elif system == 'Linux':
            # Linux espeak/festival voices (common on Raspberry Pi)
            preferred_voice_names = [
                'english',  # Generic English voice
                'en',       # English language code
            ]
        else:
            # macOS or other platforms
            preferred_voice_names = []
        
        # Try to find a preferred voice
        voice_found = False
        if preferred_voice_names:
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
        # Adjust rate for Linux (espeak tends to be faster)
        if system == 'Linux':
            _pyttsx3_engine.setProperty('rate', 150)  # Slower for espeak
        else:
            _pyttsx3_engine.setProperty('rate', 175)  # Standard rate for Windows/macOS
        _pyttsx3_engine.setProperty('volume', 0.9)  # Slightly lower for more natural sound
        
        logger.info(f"pyttsx3 engine initialized with natural voice settings (platform: {system})")
    
    return _pyttsx3_engine


def get_tts_engine():
    """Get or initialize the TTS engine."""
    return get_pyttsx3_engine()

def list_available_voices():
    """List all available TTS voices."""
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
