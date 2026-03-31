"""Play WAV files with OS-native tools (no extra Python audio deps)."""

import os
import subprocess
import sys


def play_wav(path: str) -> None:
    """Play a WAV file using built-in OS tools."""
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(path, winsound.SND_FILENAME)
    elif sys.platform == "darwin":
        subprocess.run(["afplay", path], check=True)
    else:
        for cmd in (["paplay", path], ["aplay", "-q", path]):
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        raise RuntimeError("No paplay/aplay found; install PulseAudio/ALSA utils to play WAV.")
