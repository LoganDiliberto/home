"""Light control tool for the agent."""

import logging
import json
import paho.mqtt.client as mqtt
from typing import Dict, Any, List, Optional

from core.tool import Tool

logger = logging.getLogger(__name__)

# MQTT broker configuration
MQTT_BROKER = "10.0.0.54"
MQTT_PORT = 1883

# List of available light device names
# Add more lights here as needed
AVAILABLE_LIGHTS = ["bulb1", "starter_bulb"]


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
        return "Controls lights by turning them on or off. Can control a specific light by name or all lights at once. Available lights: " + ", ".join(self.available_lights)
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "The action to perform: 'on' to turn lights on, 'off' to turn lights off"
                },
                "light_name": {
                    "type": "string",
                    "description": f"Name of the specific light to control (e.g., 'bulb1', 'starter_bulb'). Use 'all' to control all lights. Available lights: {', '.join(self.available_lights)}. If not specified, defaults to 'all'.",
                    "default": "all"
                }
            },
            "required": ["action"]
        }
    
    def _control_light(self, device_name: str, state: str) -> bool:
        """
        Control a single light via MQTT.
        
        Args:
            device_name: Name of the light device
            state: "on" or "off"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            control_topic = f"zigbee2mqtt/{device_name}/set"
            payload = {
                "state": state
            }
            
            client = mqtt.Client()
            client.connect(MQTT_BROKER, MQTT_PORT)
            client.publish(control_topic, json.dumps(payload))
            client.disconnect()
            
            logger.info(f"Successfully sent {state} command to {device_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error controlling light {device_name}: {e}", exc_info=True)
            return False
    
    def execute(self, **kwargs) -> str:
        """Execute the light control command."""
        action = kwargs.get("action", "").lower()
        light_name = kwargs.get("light_name", "all").lower()
        
        if action not in ["on", "off"]:
            return f"Error: Invalid action '{action}'. Must be 'on' or 'off'."
        
        # Normalize state for MQTT (uppercase)
        state = action.upper()
        
        # Control all lights
        if light_name == "all":
            results = []
            success_count = 0
            
            for device_name in self.available_lights:
                if self._control_light(device_name, state):
                    success_count += 1
                    results.append(f"✓ {device_name}")
                else:
                    results.append(f"✗ {device_name} (failed)")
            
            if success_count == len(self.available_lights):
                return f"Successfully turned {action} all {len(self.available_lights)} light(s)."
            elif success_count > 0:
                return f"Partially successful: turned {action} {success_count} of {len(self.available_lights)} light(s).\n" + "\n".join(results)
            else:
                return f"Error: Failed to turn {action} any lights.\n" + "\n".join(results)
        
        # Control specific light
        else:
            if light_name not in self.available_lights:
                available_str = ", ".join(self.available_lights)
                return f"Error: Unknown light '{light_name}'. Available lights: {available_str}, or use 'all' to control all lights."
            
            if self._control_light(light_name, state):
                return f"Successfully turned {action} {light_name}."
            else:
                return f"Error: Failed to turn {action} {light_name}."
