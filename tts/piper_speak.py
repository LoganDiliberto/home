"""Piper neural TTS: ONNX inference, good quality on Raspberry Pi in near real time.

Requires: pip install piper-tts
Download a voice: python -m piper.download_voices en_US-lessac-medium
Set TTS_BACKEND=piper and PIPER_MODEL or PIPER_MODEL_DIR + PIPER_VOICE.
"""

from __future__ import annotations

import logging
import os
import tempfile
import wave
from pathlib import Path
from typing import Any, Optional

from tts.playback import play_wav

logger = logging.getLogger(__name__)

_piper_voice: Any = None

DEFAULT_VOICE = "en_US-lessac-medium"

# Project root (repo root) — used to find *.onnx when cwd differs (e.g. systemd).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _truthy(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _resolve_onnx_path() -> Path:
    """Path to the Piper .onnx model file."""
    explicit = os.environ.get("PIPER_MODEL", "").strip()
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"PIPER_MODEL not found: {p}")
        return p

    # PIPER_VOICE preferred; TTS_VOICE_NAME is a legacy alias from older .env examples.
    voice = (
        os.environ.get("PIPER_VOICE", "").strip()
        or os.environ.get("TTS_VOICE_NAME", "").strip()
        or DEFAULT_VOICE
    )
    filename = f"{voice}.onnx"
    search_dirs: list[Path] = []
    env_dir = os.environ.get("PIPER_MODEL_DIR", "").strip()
    if env_dir:
        search_dirs.append(Path(env_dir).expanduser())
    search_dirs.append(_PROJECT_ROOT)
    search_dirs.append(Path.home() / ".local/share/piper")
    search_dirs.append(Path.cwd())

    for d in search_dirs:
        p = (d / filename).resolve()
        if p.is_file():
            return p

    raise FileNotFoundError(
        f"Piper model {filename} not found. Searched: "
        + ", ".join(str(d) for d in search_dirs)
        + "\nInstall: pip install piper-tts\n"
        f"Then (downloads to current directory by default): python -m piper.download_voices {voice}\n"
        "Or set PIPER_MODEL to the full path of the .onnx file, or PIPER_MODEL_DIR to its folder."
    )


def get_piper_voice():
    """Lazy singleton — loads ONNX model once (first utterance may be slower)."""
    global _piper_voice
    if _piper_voice is not None:
        return _piper_voice
    try:
        from piper import PiperVoice
    except ImportError as e:
        raise ImportError("Piper not installed. Run: pip install piper-tts") from e

    path = _resolve_onnx_path()
    use_cuda = _truthy("PIPER_USE_CUDA", default=False)
    logger.info("Loading Piper model %s (cuda=%s)", path, use_cuda)
    _piper_voice = PiperVoice.load(str(path), use_cuda=use_cuda)
    return _piper_voice


def _opt_float(name: str) -> Optional[float]:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return None
    return float(str(raw).strip())


def _maybe_synthesis_config():
    """Optional tuning via PIPER_VOLUME, PIPER_LENGTH_SCALE, etc."""
    keys = (
        "PIPER_VOLUME",
        "PIPER_LENGTH_SCALE",
        "PIPER_NOISE_SCALE",
        "PIPER_NOISE_W_SCALE",
        "PIPER_NORMALIZE",
    )
    if not any(os.environ.get(k) for k in keys):
        return None
    try:
        from piper import SynthesisConfig
    except ImportError:
        return None

    vol_raw = os.environ.get("PIPER_VOLUME")
    volume = float(vol_raw.strip()) if vol_raw and str(vol_raw).strip() else 1.0
    norm_raw = os.environ.get("PIPER_NORMALIZE")
    if norm_raw is not None and str(norm_raw).strip():
        normalize_audio = _truthy("PIPER_NORMALIZE", default=True)
    else:
        normalize_audio = True

    return SynthesisConfig(
        volume=volume,
        length_scale=_opt_float("PIPER_LENGTH_SCALE"),
        noise_scale=_opt_float("PIPER_NOISE_SCALE"),
        noise_w_scale=_opt_float("PIPER_NOISE_W_SCALE"),
        normalize_audio=normalize_audio,
    )


def speak_piper(text: str) -> None:
    """Synthesize with Piper and play the WAV."""
    voice = get_piper_voice()
    cfg = _maybe_synthesis_config()
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        with wave.open(wav_path, "wb") as wav_file:
            if cfg is not None:
                voice.synthesize_wav(text, wav_file, syn_config=cfg)
            else:
                voice.synthesize_wav(text, wav_file)
        play_wav(wav_path)
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


def describe_piper_config() -> str:
    """Non-destructive summary for startup logging (does not load the ONNX model)."""
    import importlib.util

    if importlib.util.find_spec("piper") is None:
        return "piper-tts not installed (pip install piper-tts)"
    try:
        path = _resolve_onnx_path()
        return f"model: {path}"
    except OSError as e:
        return str(e)
