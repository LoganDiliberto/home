"""Light control command handlers."""

import logging
import re
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from core.command import Command

from commands.tools.light_tool import (
    AVAILABLE_LIGHTS,
    apply_qualitative_adjustments,
    build_light_payload,
    fetch_device_state,
    publish_light_set,
)

if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)

# Voice commands target the first configured light unless we add multi-light parsing later.
DEFAULT_LIGHT = AVAILABLE_LIGHTS[0] if AVAILABLE_LIGHTS else "bulb1"

# Spoken color names -> (hue, saturation) or Kelvin for whites
_COLOR_HUE: Dict[str, Tuple[int, int]] = {
    "red": (0, 100),
    "orange": (35, 100),
    "yellow": (55, 100),
    "green": (120, 100),
    "cyan": (180, 100),
    "blue": (240, 100),
    "purple": (270, 100),
    "violet": (270, 100),
    "pink": (330, 85),
    "magenta": (300, 100),
}
_COLOR_KELVIN: Dict[str, int] = {
    "warm": 2700,
    "warmth": 2700,
    "warm white": 2700,
    "cool": 5000,
    "cool white": 5000,
    "daylight": 5500,
    "white": 4000,
}


def _parse_brightness_percent(command: str) -> Optional[int]:
    """Extract a 0-100 brightness percentage from spoken text."""
    lower = command.lower()
    for pattern in (
        r"(?:brightness|bright|dim)\D+(\d{1,3})\s*(?:%|percent)?",
        r"(\d{1,3})\s*(?:%|percent)\D*light",
        r"light\D+(\d{1,3})\s*(?:%|percent)",
        r"(\d{1,3})\s*percent\D*light",
        r"light\D+(\d{1,3})\s*(?:%|percent)?\b",
        r"(?:set\s+)?light\s+to\s+(\d{1,3})\s*(?:%|percent)?\b",
    ):
        m = re.search(pattern, lower)
        if m:
            v = int(m.group(1))
            return max(0, min(100, v))
    m = re.search(r"\b(\d{1,3})\s*(?:%|percent)\b", lower)
    if m and "light" in lower:
        v = int(m.group(1))
        return max(0, min(100, v))
    return None


def _parse_color(command: str) -> Optional[Tuple[str, int, Optional[int]]]:
    """Return ('kelvin', kelvin, None) or ('hue', hue, saturation)."""
    lower = command.lower()
    for phrase, k in sorted(_COLOR_KELVIN.items(), key=lambda x: -len(x[0])):
        esc = r"\s+".join(re.escape(p) for p in phrase.split())
        if re.search(rf"\b{esc}\b", lower):
            return ("kelvin", k, None)
    for word, (h, s) in _COLOR_HUE.items():
        if re.search(rf"\b{re.escape(word)}\b", lower):
            return ("hue", h, s)
    return None


def _voice_named_color_token(c: str) -> Optional[str]:
    """Longest matching color name token, or None."""
    lower = c.lower()
    for phrase in sorted(_COLOR_KELVIN.keys(), key=len, reverse=True):
        esc = r"\s+".join(re.escape(p) for p in phrase.split())
        if re.search(rf"\b{esc}\b", lower):
            return phrase
    for word in sorted(_COLOR_HUE.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(word)}\b", lower):
            return word
    return None


def _voice_brightness_change(c: str) -> Optional[str]:
    """Map speech to brightness_change enum; None if not a relative brightness request."""
    c = c.lower()
    much = bool(re.search(r"\b(much|a lot|way)\b", c))
    slight = bool(re.search(r"\b(a little|slightly|tiny bit|a bit)\b", c))

    dim = bool(
        re.search(r"\b(dim|dimmer)\b", c)
        or "brightness down" in c
        or "lower brightness" in c
        or "turn down brightness" in c
        or "turn down the brightness" in c
        or "less bright" in c
    )
    up = bool(
        re.search(r"\b(brighter|brighten)\b", c)
        or "brightness up" in c
        or "raise brightness" in c
        or "turn up brightness" in c
        or "turn up the brightness" in c
        or "more bright" in c
    )
    if not dim and not up:
        return None
    if dim and up:
        return "dimmer"
    if dim:
        if much:
            return "much_dimmer"
        if slight:
            return "slightly_dimmer"
        return "dimmer"
    if much:
        return "much_brighter"
    if slight:
        return "slightly_brighter"
    return "brighter"


def _voice_color_adjustment(c: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Map speech to (color_adjustment enum or None, named_color or None).
    """
    c = c.lower()
    nc = _voice_named_color_token(c)
    ca: Optional[str] = None

    if re.search(r"\bwarmer\b", c):
        ca = "warmer"
    elif re.search(r"\bcooler\b", c):
        ca = "cooler"
    elif "more vibrant" in c or "more saturated" in c:
        ca = "more_vibrant"
    elif "more muted" in c or "less saturated" in c:
        ca = "more_muted"
    elif re.search(r"\bvibrant\b", c) and "less" not in c:
        ca = "more_vibrant"
    elif re.search(r"\bmuted\b", c):
        ca = "more_muted"
    elif re.search(r"\blighter\b", c):
        ca = "lighter"
    elif re.search(r"\bdarker\b", c):
        ca = "darker"

    if ca is None:
        return None, None
    return ca, nc


def _has_qualitative_modifier(c: str) -> bool:
    return _voice_brightness_change(c) is not None or _voice_color_adjustment(c)[0] is not None


class TurnOnLightCommand(Command):
    """Command to turn on lights."""

    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn on' and 'light'."""
        return "turn on" in command and "light" in command

    def execute(self, command: str, services: "ServiceContainer") -> str:
        """Execute turn on light command."""
        logger.info("Light control command detected: turn on")
        payload = build_light_payload("on")
        if not payload or not publish_light_set(DEFAULT_LIGHT, payload):
            return "Could not turn on the light"
        return "Turning lights on"

    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5


class TurnOffLightCommand(Command):
    """Command to turn off lights."""

    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn off' and 'light'."""
        return "turn off" in command and "light" in command

    def execute(self, command: str, services: "ServiceContainer") -> str:
        """Execute turn off light command."""
        logger.info("Light control command detected: turn off")
        payload = build_light_payload("off")
        if not payload or not publish_light_set(DEFAULT_LIGHT, payload):
            return "Could not turn off the light"
        return "Turning lights off"

    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5


class QualitativeLightAdjustCommand(Command):
    """Adjust brightness or color using words only (no percentages)."""

    def can_handle(self, command: str) -> bool:
        c = command.lower()
        if "light" not in c:
            return False
        if _parse_brightness_percent(c) is not None:
            return False
        bc = _voice_brightness_change(c)
        ca, _ = _voice_color_adjustment(c)
        return bc is not None or ca is not None

    def execute(self, command: str, services: "ServiceContainer") -> str:
        logger.info("Qualitative light adjust command detected")
        c = command.lower()
        bc = _voice_brightness_change(c)
        ca, nc = _voice_color_adjustment(c)
        if bc is None and ca is None:
            return "Could not understand that lighting change"

        need_fetch = bool(bc or (ca is not None and nc is None))
        st = fetch_device_state(DEFAULT_LIGHT) if need_fetch else None

        bp, h, s, k, err = apply_qualitative_adjustments(
            state=st,
            brightness_change=bc,
            color_adjustment=ca,
            named_color=nc,
        )
        if err:
            return err

        payload = build_light_payload("on", brightness_percent=bp, hue=h, saturation=s, color_temp_kelvin=k)
        if not payload or not publish_light_set(DEFAULT_LIGHT, payload):
            return "Could not adjust the lights"

        parts = []
        if bc:
            parts.append(bc.replace("_", " "))
        if ca:
            parts.append(ca.replace("_", " "))
        if nc:
            parts.append(nc)
        return "Okay, adjusting the lights: " + ", ".join(parts)

    def get_priority(self) -> int:
        return 11


class SetLightBrightnessCommand(Command):
    """Set light brightness by spoken percentage."""

    def can_handle(self, command: str) -> bool:
        c = command.lower()
        if "light" not in c:
            return False
        if _parse_brightness_percent(c) is None:
            return False
        return any(
            x in c
            for x in ("brightness", "bright", "dim", "%", "percent", "lighter", "darker")
        ) or "light to " in c

    def execute(self, command: str, services: "ServiceContainer") -> str:
        logger.info("Light brightness command detected")
        pct = _parse_brightness_percent(command.lower())
        if pct is None:
            return "Could not understand the brightness level"
        payload = build_light_payload("set", brightness_percent=pct)
        if not payload or not publish_light_set(DEFAULT_LIGHT, payload):
            return "Could not set brightness"
        return f"Setting light to {pct} percent"

    def get_priority(self) -> int:
        return 10


class SetLightColorCommand(Command):
    """Set light color from spoken color names (hue or white temperature)."""

    def can_handle(self, command: str) -> bool:
        c = command.lower()
        if "light" not in c:
            return False
        if _has_qualitative_modifier(c):
            return False
        return _parse_color(c) is not None

    def execute(self, command: str, services: "ServiceContainer") -> str:
        logger.info("Light color command detected")
        parsed = _parse_color(command.lower())
        if not parsed:
            return "Could not understand the color"
        kind, a, b = parsed
        if kind == "kelvin":
            payload = build_light_payload("on", color_temp_kelvin=a)
            msg = f"Setting light to {a} kelvin"
        else:
            payload = build_light_payload("on", hue=a, saturation=b or 100)
            msg = "Setting light color"
        if not payload or not publish_light_set(DEFAULT_LIGHT, payload):
            return "Could not set color"
        return msg

    def get_priority(self) -> int:
        return 10
