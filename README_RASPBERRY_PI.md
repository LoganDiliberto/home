# Raspberry Pi Setup Instructions

This guide will help you set up the voice assistant on a Raspberry Pi running Raspberry Pi OS (Debian-based Linux).

## System Requirements

- Raspberry Pi (any model, but Pi 4 or newer recommended)
- Raspberry Pi OS (or other Debian-based Linux distribution)
- Python 3.8 or higher
- Microphone and speakers/headphones

## System Package Installation

Before installing Python packages, you need to install system dependencies:

```bash
# Update package list
sudo apt-get update

# Install audio dependencies for PyAudio
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Install TTS engine (espeak) for pyttsx3
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Alternative: Install festival TTS (optional, if you prefer festival over espeak)
# sudo apt-get install -y festival festival-dev
```

## Python Package Installation

1. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Application

```bash
python talk.py
```

## Troubleshooting

### PyAudio Installation Issues

If you get errors installing PyAudio, make sure you've installed the system packages:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

### TTS Voice Issues

If TTS doesn't work or sounds robotic:
1. Check available voices: The code will automatically use available espeak voices
2. Install additional voices: `sudo apt-get install espeak-data`
3. Test espeak directly: `espeak "Hello, this is a test"`

### Audio Input/Output Issues

- Make sure your microphone is recognized: `arecord -l`
- Test microphone: `arecord -d 5 test.wav && aplay test.wav`
- Check audio output: `aplay /usr/share/sounds/alsa/Front_Left.wav`

### MQTT Connection Issues

If light control doesn't work:
- Verify MQTT broker is accessible from your Pi
- Check network connectivity: `ping <mqtt_broker_ip>`
- Test MQTT connection: `mosquitto_pub -h <broker_ip> -t test -m "hello"`

## Differences from Windows Version

- **TTS Engine**: Uses espeak instead of Windows SAPI
- **Voice Names**: Different voice names (espeak uses language codes)
- **Audio Backend**: Uses ALSA/PulseAudio instead of DirectSound
- **No Windows-specific packages**: No need for pypiwin32 or comtypes

## Performance Tips

- Use a USB microphone for better quality
- Consider using a USB audio adapter if onboard audio has issues
- For better TTS quality, you might want to use a cloud TTS service instead of espeak
