"""Light control tool for the agent."""

import json
import logging
import threading
import time
import paho.mqtt.client as mqtt
from typing import Any, Dict, List, Optional, Tuple

from core.tool import Tool

logger = logging.getLogger(__name__)

# MQTT broker configuration
MQTT_BROKER = "10.0.0.54"
MQTT_PORT = 1883

# List of available light device names
# Add more lights here as needed
AVAILABLE_LIGHTS = ["bulb1", "bulb2", "kitchenlight"]

# Relative brightness deltas (percent points) for brightness_change tokens
_BRIGHTNESS_DELTA = {
    "slightly_dimmer": -8,
    "dimmer": -18,
    "much_dimmer": -30,
    "slightly_brighter": 8,
    "brighter": 18,
    "much_brighter": 30,
}

# Qualitative color adjustments (applied on top of current state or named_color base)
_COLOR_SAT_DELTA = {
    "more_vibrant": 22,
    "more_saturated": 22,
    "more_muted": -22,
    "less_saturated": -22,
}
_COLOR_BRIGHTNESS_DELTA = {
    "darker": -16,
    "lighter": 16,
}
_KELVIN_DELTA = {
    "warmer": -350,
    "cooler": 350,
}

# When state cannot be read but user gave named_color + adjustment, use these defaults
_NAMED_COLOR_DEFAULT_BRIGHTNESS_PCT = 55


def fetch_device_state(device_name: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Read current Zigbee2MQTT device state (subscribe + /get trigger).
    Returns parsed JSON from zigbee2mqtt/{device} or None on failure.
    """
    result: Dict[str, Any] = {}
    received = threading.Event()

    def on_message(_client: Any, _userdata: Any, msg: Any) -> None:
        try:
            data = json.loads(msg.payload.decode())
            if isinstance(data, dict) and (
                "brightness" in data or "state" in data or "color" in data or "color_temp" in data
            ):
                result.clear()
                result.update(data)
                received.set()
        except Exception:
            pass

    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.subscribe(f"zigbee2mqtt/{device_name}")
        client.loop_start()
        time.sleep(0.08)
        client.publish(f"zigbee2mqtt/{device_name}/get", "{}", qos=0)
        if not received.wait(timeout):
            client.loop_stop()
            client.disconnect()
            return None
        client.loop_stop()
        client.disconnect()
        return dict(result)
    except Exception as e:
        logger.error(f"fetch_device_state failed for {device_name}: {e}", exc_info=True)
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
        return None


def _brightness_pct_from_state(state: Dict[str, Any]) -> int:
    b = state.get("brightness")
    if b is None:
        return 50 if str(state.get("state", "")).upper() == "ON" else 0
    return int(max(0, min(100, round(int(b) / 254.0 * 100))))


def _hue_sat_from_state(state: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    c = state.get("color")
    if isinstance(c, dict) and "hue" in c:
        return int(c["hue"]) % 360, int(max(0, min(100, c.get("saturation", 100))))
    return None


def _kelvin_from_state(state: Dict[str, Any]) -> Optional[int]:
    m = state.get("color_temp")
    if m is not None:
        return int(max(2000, min(6500, round(1e6 / float(m)))))
    return None


def _named_color_to_hue_sat(name: str) -> Optional[Tuple[int, int]]:
    from commands.light_commands import _COLOR_HUE  # circular? light_commands imports light_tool

    # Avoid circular import: inline minimal map
    table = {
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
    key = name.strip().lower()
    return table.get(key)


def _named_color_to_kelvin(name: str) -> Optional[int]:
    table = {
        "warm": 2700,
        "warm white": 2700,
        "cool": 5000,
        "cool white": 5000,
        "daylight": 5500,
        "white": 4000,
    }
    return table.get(name.strip().lower())


def apply_qualitative_adjustments(
    *,
    state: Optional[Dict[str, Any]],
    brightness_percent: Optional[int] = None,
    hue: Optional[int] = None,
    saturation: Optional[int] = None,
    color_temp_kelvin: Optional[int] = None,
    brightness_change: Optional[str] = None,
    color_adjustment: Optional[str] = None,
    named_color: Optional[str] = None,
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int], Optional[str]]:
    """
    Merge absolute args with qualitative adjustments. Returns
    (brightness_pct, hue, saturation, kelvin, error).
    Omitted brightness stays None unless a qualitative rule sets it.
    """
    err: Optional[str] = None
    bc_raw = brightness_change.lower().strip() if brightness_change else None
    # Explicit brightness wins over relative brightness
    bc = None if brightness_percent is not None else bc_raw
    ca = color_adjustment.lower().strip() if color_adjustment else None

    if bc and bc not in _BRIGHTNESS_DELTA:
        err = f"Unknown brightness_change '{brightness_change}'"
        return None, None, None, None, err
    if ca:
        allowed = set(_COLOR_SAT_DELTA) | set(_COLOR_BRIGHTNESS_DELTA) | set(_KELVIN_DELTA)
        if ca not in allowed:
            err = f"Unknown color_adjustment '{color_adjustment}'"
            return None, None, None, None, err

    bp = brightness_percent
    h, s = hue, saturation
    k = color_temp_kelvin

    # Pull hue/sat/kelvin/bp from device state when needed for qualitative changes
    hs = _hue_sat_from_state(state) if state else None
    if state:
        if bc and bp is None:
            bp = _brightness_pct_from_state(state)
        if ca in _COLOR_SAT_DELTA or ca in _COLOR_BRIGHTNESS_DELTA:
            if hs and h is None and s is None:
                h, s = hs
            if ca in _COLOR_BRIGHTNESS_DELTA and bp is None:
                bp = _brightness_pct_from_state(state)
        if ca in _KELVIN_DELTA and k is None:
            k = _kelvin_from_state(state)

    if named_color:
        nk = _named_color_to_kelvin(named_color)
        nh = _named_color_to_hue_sat(named_color)
        if nh:
            if h is None:
                h, s = nh
            if bp is None and (ca or bc):
                bp = _NAMED_COLOR_DEFAULT_BRIGHTNESS_PCT
        elif nk is not None:
            if k is None:
                k = nk
            if bp is None and (ca or bc):
                bp = _NAMED_COLOR_DEFAULT_BRIGHTNESS_PCT

    if bc and bp is None:
        bp = 50

    if bc:
        bp = max(0, min(100, bp + _BRIGHTNESS_DELTA[bc]))

    if ca in _COLOR_SAT_DELTA:
        if h is None and named_color:
            nh = _named_color_to_hue_sat(named_color)
            if nh:
                h, s = nh[0], nh[1]
        if s is None:
            s = 80
        s = max(0, min(100, s + _COLOR_SAT_DELTA[ca]))
        if h is None:
            err = "Cannot change saturation without a color (hue), named_color, or readable light state."
            return None, None, None, None, err
    elif ca in _COLOR_BRIGHTNESS_DELTA:
        if bp is None:
            bp = _NAMED_COLOR_DEFAULT_BRIGHTNESS_PCT
        bp = max(0, min(100, bp + _COLOR_BRIGHTNESS_DELTA[ca]))
        if h is not None and s is not None:
            if ca == "darker":
                s = min(100, s + 6)
            else:
                s = max(0, s - 6)
    elif ca in _KELVIN_DELTA:
        if k is None:
            nk = _named_color_to_kelvin(named_color) if named_color else None
            k = nk if nk is not None else 4000
        k = max(2000, min(6500, k + _KELVIN_DELTA[ca]))

    return bp, h, s, k, err


def publish_light_set(device_name: str, payload: Dict[str, Any]) -> bool:
    """Publish a Zigbee2MQTT /set payload for one device."""
    try:
        control_topic = f"zigbee2mqtt/{device_name}/set"
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.publish(control_topic, json.dumps(payload))
        client.disconnect()
        logger.info(f"Published to {device_name}: {payload}")
        return True
    except Exception as e:
        logger.error(f"Error publishing to {device_name}: {e}", exc_info=True)
        return False


def build_light_payload(
    action: str,
    brightness_percent: Optional[int] = None,
    hue: Optional[int] = None,
    saturation: Optional[int] = None,
    color_temp_kelvin: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build a Zigbee2MQTT payload for lights.

    action: 'on', 'off', or 'set' (brightness/color only; device may turn on when levels change).
    """
    action = action.lower()
    if action not in ("on", "off", "set"):
        return None

    if action == "off":
        return {"state": "OFF"}

    payload: Dict[str, Any] = {}

    if action == "on":
        payload["state"] = "ON"

    if brightness_percent is not None:
        b = max(0, min(100, int(brightness_percent)))
        payload["brightness"] = int(round(b / 100.0 * 254))

    if color_temp_kelvin is not None:
        k = max(2000, min(6500, int(color_temp_kelvin)))
        payload["color_temp"] = int(round(1e6 / k))
    elif hue is not None:
        h = int(hue) % 360
        sat = 100 if saturation is None else max(0, min(100, int(saturation)))
        payload["color"] = {"hue": h, "saturation": sat}

    if action == "set" and not payload:
        return None

    return payload


class LightTool(Tool):
    """Tool for controlling lights via MQTT."""

    def __init__(self, available_lights: Optional[List[str]] = None):
        """
        Initialize the light tool.

        Args:
            available_lights: List of light device names. If None, uses default list.
        """
        self.available_lights = available_lights or AVAILABLE_LIGHTS

    def name(self) -> str:
        """Get the tool name."""
        return "control_lights"

    def description(self) -> str:
        """Get the tool description."""
        return (
            "Controls Zigbee lights via MQTT. Prefer qualitative controls when the user does NOT "
            "give a number: use brightness_change (dimmer/brighter steps) and color_adjustment "
            "(more_vibrant, darker, warmer, etc.) instead of asking for percentages. "
            "Numbers are optional. For 'darker red' or 'muted blue', set named_color plus "
            "color_adjustment. Relative changes read the current light state when possible. "
            "Available lights: "
            + ", ".join(self.available_lights)
        )

    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["on", "off", "set"],
                    "description": (
                        "'on' / 'off' switch the light; 'set' only applies brightness/color "
                        "(light often turns on when brightness is set)"
                    ),
                },
                "light_name": {
                    "type": "string",
                    "description": (
                        f"Light to control (e.g. 'bulb1'). Use 'all' for every light. "
                        f"Available: {', '.join(self.available_lights)}. Default: 'all'."
                    ),
                    "default": "all",
                },
                "brightness_percent": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Exact brightness 0-100. Omit if using brightness_change instead.",
                },
                "brightness_change": {
                    "type": "string",
                    "enum": list(_BRIGHTNESS_DELTA.keys()),
                    "description": (
                        "Relative brightness when the user does not give a number: e.g. dimmer, "
                        "brighter, a bit dimmer, much brighter. Do not ask for a percentage."
                    ),
                },
                "hue": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 360,
                    "description": "Hue in degrees. Omit if using color_temp_kelvin or named_color.",
                },
                "saturation": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Saturation 0-100. Usually omit; use color_adjustment instead.",
                },
                "color_temp_kelvin": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 6500,
                    "description": "White tone in Kelvin. Omit if using qualitative adjustments.",
                },
                "color_adjustment": {
                    "type": "string",
                    "enum": sorted(
                        set(_COLOR_SAT_DELTA) | set(_COLOR_BRIGHTNESS_DELTA) | set(_KELVIN_DELTA)
                    ),
                    "description": (
                        "Qualitative color change without numbers: more_vibrant, more_muted, darker, "
                        "lighter, warmer, cooler. Combine with named_color for 'darker red'."
                    ),
                },
                "named_color": {
                    "type": "string",
                    "description": (
                        "Color name for qualitative phrases: red, blue, warm white, etc. "
                        "Use with color_adjustment (e.g. darker + red)."
                    ),
                },
            },
            "required": ["action"],
        }

    def _control_light_resolved(
        self,
        device_name: str,
        action: str,
        brightness_percent: Optional[int],
        hue: Optional[int],
        saturation: Optional[int],
        color_temp_kelvin: Optional[int],
    ) -> bool:
        payload = build_light_payload(
            action,
            brightness_percent=brightness_percent,
            hue=hue,
            saturation=saturation,
            color_temp_kelvin=color_temp_kelvin,
        )
        if payload is None:
            return False
        return publish_light_set(device_name, payload)

    def execute(self, **kwargs) -> str:
        """Execute the light control command."""
        action = kwargs.get("action", "").lower()
        light_name = kwargs.get("light_name", "all").lower()

        brightness = kwargs.get("brightness_percent")
        if brightness is not None:
            brightness = int(brightness)

        hue = kwargs.get("hue")
        if hue is not None:
            hue = int(hue)

        saturation = kwargs.get("saturation")
        if saturation is not None:
            saturation = int(saturation)

        ct = kwargs.get("color_temp_kelvin")
        if ct is not None:
            ct = int(ct)

        brightness_change = kwargs.get("brightness_change")
        if brightness_change is not None:
            brightness_change = str(brightness_change).strip()

        color_adjustment = kwargs.get("color_adjustment")
        if color_adjustment is not None:
            color_adjustment = str(color_adjustment).strip()

        named_color = kwargs.get("named_color")
        if named_color is not None:
            named_color = str(named_color).strip()

        if action not in ("on", "off", "set"):
            return f"Error: Invalid action '{action}'. Must be 'on', 'off', or 'set'."

        has_qualitative = bool(brightness_change or color_adjustment or named_color)
        has_absolute = (
            brightness is not None or hue is not None or saturation is not None or ct is not None
        )

        targets = self.available_lights if light_name == "all" else [light_name]

        if light_name != "all" and light_name not in self.available_lights:
            available_str = ", ".join(self.available_lights)
            return f"Error: Unknown light '{light_name}'. Available: {available_str}, or 'all'."

        if action == "off":
            ok = 0
            for device_name in targets:
                if self._control_light_resolved(device_name, "off", None, None, None, None):
                    ok += 1
            if ok == len(targets):
                return f"Successfully turned off {len(targets)} light(s)."
            if ok == 0:
                return "Error: Failed to turn off lights."
            return f"Partial success: turned off {ok} of {len(targets)} light(s)."

        if action == "set" and not has_qualitative and not has_absolute:
            return (
                "Error: action 'set' needs brightness_percent, hue/color_temp_kelvin, or qualitative "
                "fields (brightness_change, color_adjustment, named_color)."
            )

        if action == "on" and not has_qualitative and not has_absolute:
            ok = 0
            for device_name in targets:
                if publish_light_set(device_name, {"state": "ON"}):
                    ok += 1
            if ok == len(targets):
                return f"Successfully turned on {len(targets)} light(s)."
            if ok == 0:
                return "Error: Failed to turn on lights."
            return f"Partial success: turned on {ok} of {len(targets)} light(s)."

        results: List[str] = []
        success_count = 0
        last_bp, last_h, last_s, last_k = brightness, hue, saturation, ct
        eff_action = action

        need_fetch = bool(
            (brightness_change and brightness is None)
            or (color_adjustment and not named_color)
        )

        for device_name in targets:
            state = fetch_device_state(device_name) if need_fetch else None

            bp, h, s, k, err = apply_qualitative_adjustments(
                state=state,
                brightness_percent=brightness,
                hue=hue,
                saturation=saturation,
                color_temp_kelvin=ct,
                brightness_change=brightness_change,
                color_adjustment=color_adjustment,
                named_color=named_color,
            )
            if err:
                return f"Error: {err}"

            eff_action = action
            if eff_action == "set" and has_qualitative and not has_absolute:
                eff_action = "on"

            if not self._control_light_resolved(device_name, eff_action, bp, h, s, k):
                results.append(f"✗ {device_name} (failed)")
            else:
                success_count += 1
                results.append(f"✓ {device_name}")
                last_bp, last_h, last_s, last_k = bp, h, s, k

        n = len(targets)
        extras = self._extras(last_bp, last_k, last_h, last_s, brightness_change, color_adjustment)
        detail = f" ({', '.join(extras)})" if extras else ""

        if success_count == n:
            if action == "on" or eff_action == "on":
                return f"Successfully turned on {n} light(s){detail}."
            return f"Successfully updated {n} light(s){detail}."

        if success_count > 0:
            return (
                f"Partial success: {success_count} of {n} lights.{detail}\n" + "\n".join(results)
            )
        return f"Error: Failed for all lights.\n" + "\n".join(results)

    def _extras(
        self,
        bp: Optional[int],
        k: Optional[int],
        h: Optional[int],
        s: Optional[int],
        brightness_change: Optional[str],
        color_adjustment: Optional[str],
    ) -> List[str]:
        out: List[str] = []
        if bp is not None:
            out.append(f"brightness ~{bp}%")
        if k is not None:
            out.append(f"{k} K")
        elif h is not None:
            sat = s if s is not None else 100
            out.append(f"hue {h}° sat {sat}%")
        if brightness_change:
            out.append(brightness_change.replace("_", " "))
        if color_adjustment:
            out.append(color_adjustment.replace("_", " "))
        return out
