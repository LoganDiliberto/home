# Voice Cloning with Coqui TTS

This directory contains tools for recording and cloning voices using Coqui TTS (XTTS v2) for use in the voice assistant.

## Overview

The voice cloning system allows you to:
1. Record your voice (or any voice) using a microphone
2. Clone the voice using Coqui TTS neural network models
3. Use the cloned voice in `talk.py` for natural-sounding speech synthesis

## Requirements

- Python 3.8+
- Coqui TTS library (installed via `pip install TTS`)
- PyAudio (for recording)
- A microphone for recording

## Quick Start

### 1. Record a Voice

Run the recording script to capture audio:

```bash
python tts/record_voice.py
```

The script will:
- Prompt you for a voice name
- Record audio from your microphone (30-60 seconds recommended)
- Save the recording to `tts/recordings/<voice_name>.wav`
- Validate the recording quality

**Tips for best results:**
- Record in a quiet environment
- Speak naturally and clearly
- Use 30-60 seconds of varied speech
- Avoid background noise
- Speak at a normal pace

### 2. Clone the Voice

After recording, clone the voice:

```bash
python tts/clone_voice.py <voice_name>
```

Or run interactively:

```bash
python tts/clone_voice.py
```

The script will:
- Load your recording
- Initialize the Coqui TTS XTTS v2 model (downloads ~1.5GB on first run)
- Create a voice clone/embedding
- Save it to `tts/voices/<voice_name>/`
- Generate a test sample

**Note:** The first run will download the XTTS v2 model, which may take several minutes depending on your internet connection.

### 3. Use the Cloned Voice

To use your cloned voice in `talk.py`:

1. Set environment variables in your `.env` file:
   ```
   TTS_ENGINE=coqui
   TTS_VOICE_NAME=<your_voice_name>
   COQUI_DEVICE=cpu  # or "cuda" if you have a GPU
   ```

2. Run the voice assistant:
   ```bash
   python talk.py
   ```

The assistant will now use your cloned voice for all responses.

## Directory Structure

```
tts/
├── __init__.py
├── record_voice.py      # Interactive voice recording script
├── clone_voice.py       # Voice cloning script
├── voice_manager.py     # Utility functions
├── README.md            # This file
├── recordings/          # Raw audio recordings
│   └── <voice_name>.wav
└── voices/              # Cloned voice data
    └── <voice_name>/
        ├── voice.wav    # Reference audio
        └── test_output.wav  # Test sample
```

## Scripts

### record_voice.py

Interactive script for recording voice samples.

**Usage:**
```bash
python tts/record_voice.py
```

**Features:**
- Interactive prompts for voice name and duration
- Real-time recording with progress display
- Automatic validation of recording quality
- Support for 10-120 seconds of audio

### clone_voice.py

Script for cloning voices from recordings.

**Usage:**
```bash
# With voice name
python tts/clone_voice.py my_voice

# Interactive mode (lists available recordings)
python tts/clone_voice.py

# List available recordings
python tts/clone_voice.py --list
```

**Options:**
- `--device cpu|cuda`: Choose device for inference (default: cpu)
- `--list`: List all available recordings

### voice_manager.py

Utility module with helper functions:
- `list_cloned_voices()`: List all cloned voices
- `list_recordings()`: List all recordings
- `validate_recording(file_path)`: Validate audio file quality
- `get_voice_path(voice_name)`: Get path to cloned voice
- `get_recording_path(voice_name)`: Get path to recording

## Audio Requirements

For best results, recordings should:
- **Duration:** 30-60 seconds (minimum 10, maximum 120)
- **Format:** WAV format
- **Sample Rate:** 16kHz or higher (22.05kHz recommended)
- **Channels:** Mono (stereo will be converted automatically)
- **Quality:** Clear audio with minimal background noise
- **Content:** Natural speech with varied intonation

## Performance Notes

- **CPU vs GPU:** Coqui TTS works on CPU but is slower. GPU (CUDA) is recommended for faster synthesis.
- **First Run:** The first time you run `clone_voice.py`, it will download the XTTS v2 model (~1.5GB).
- **Synthesis Speed:** Voice synthesis is slower than pyttsx3 but produces more natural results.
- **Model Size:** The XTTS v2 model is large but only needs to be downloaded once.

## Troubleshooting

### "TTS library not installed"
Install Coqui TTS:
```bash
pip install TTS
```

### "Recording too short/too long"
Ensure your recording is between 10-120 seconds. 30-60 seconds is recommended.

### "Cloned voice not found"
Make sure you've run `clone_voice.py` after recording. Check that the voice exists in `tts/voices/<voice_name>/`.

### "Error initializing Coqui TTS"
- Check that TTS is installed: `pip install TTS`
- Verify the voice directory exists and contains `voice.wav`
- Check the logs for detailed error messages

### Slow synthesis
- Use GPU if available: Set `COQUI_DEVICE=cuda` in `.env`
- Consider using pyttsx3 for faster (but less natural) speech

## Switching Between TTS Engines

To switch back to pyttsx3 (system voices):

```env
TTS_ENGINE=pyttsx3
```

Or remove the `TTS_ENGINE` variable (pyttsx3 is the default).

To use a cloned voice:

```env
TTS_ENGINE=coqui
TTS_VOICE_NAME=my_voice
```

## Listing Available Voices

To see all available voices (both system and cloned):

```python
from talk import list_available_voices
list_available_voices()
```

Or check the directories:
- System voices: Managed by Windows/pyttsx3
- Cloned voices: `tts/voices/` directory

## Best Practices

1. **Recording Quality:**
   - Use a good microphone if possible
   - Record in a quiet room
   - Speak naturally, not too fast or slow
   - Include varied sentence types (questions, statements, etc.)

2. **Voice Selection:**
   - Use descriptive names for your voices
   - Keep recordings organized
   - Test cloned voices before using in production

3. **Performance:**
   - Use GPU for faster synthesis if available
   - Consider caching frequently used phrases
   - Monitor system resources during synthesis

## Technical Details

- **Model:** Coqui TTS XTTS v2 (multilingual, multi-dataset)
- **Voice Cloning:** Zero-shot voice cloning (no training required)
- **Supported Languages:** Multiple languages (English recommended)
- **Audio Format:** WAV, 16kHz+ sample rate, mono

## License

This voice cloning system uses Coqui TTS, which is licensed under the MPL 2.0 license. See the Coqui TTS repository for details.

