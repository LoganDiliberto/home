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
AVAILABLE_PLUGS = ["smartplug1"]


class PlugTool(Tool):
    """Tool for controlling plugs via MQTT."""
    
    def __init__(self, available_plugs: Optional[List[str]] = None):
        """
        Initialize the plug tool.
        
        Args:
            available_plugs: List of plug device names. If None, uses default list.
        """
        self.available_plugs = available_plugs or AVAILABLE_PLUGS
    
    def name(self) -> str:
        """Get the tool name."""
        return "control_plugs"
    
    def description(self) -> str:
        """Get the tool description."""
        return "Controls plugs by turning them on or off. Can control a specific plug by name or all plugs at once. Available plugs: " + ", ".join(self.available_plugs)
    
    def parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["on", "off"],
                    "description": "The action to perform: 'on' to turn plugs on, 'off' to turn plugs off"
                },
                "plug_name": {
                    "type": "string",
                    "description": f"Name of the specific plug to control (e.g., 'smartplug1'). Use 'all' to control all plugs. Available plugs: {', '.join(self.available_plugs)}. If not specified, defaults to 'all'.",
                    "default": "all"
                }
            },
            "required": ["action"]
        }
    
    def _control_plug(self, device_name: str, state: str) -> bool:
        """
        Control a single plug via MQTT.
        
        Args:
            plug_name: Name of the plug device
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
            logger.error(f"Error controlling plug {device_name}: {e}", exc_info=True)
            return False
    
    def execute(self, **kwargs) -> str:
        """Execute the plug control command."""
        action = kwargs.get("action", "").lower()
        plug_name = kwargs.get("plug_name", "all").lower()
        
        if action not in ["on", "off"]:
            return f"Error: Invalid action '{action}'. Must be 'on' or 'off'."
        
        # Normalize state for MQTT (uppercase)
        state = action.upper()
        
        # Control all lights
        if plug_name == "all":
            results = []
            success_count = 0
            
            for device_name in self.available_lights:
                if self._control_plug(device_name, state):
                    success_count += 1
                    results.append(f"✓ {device_name}")
                else:
                    results.append(f"✗ {device_name} (failed)")
            
            if success_count == len(self.available_plugs):
                return f"Successfully turned {action} all {len(self.available_plugs)} plug(s)."
            elif success_count > 0:
                return f"Partially successful: turned {action} {success_count} of {len(self.available_lights)} light(s).\n" + "\n".join(results)
            else:
                return f"Error: Failed to turn {action} any plugs.\n" + "\n".join(results)
        
        # Control specific plug
        else:
            if plug_name not in self.available_plugs:
                available_str = ", ".join(self.available_plugs)
                return f"Error: Unknown plug '{plug_name}'. Available plugs: {available_str}, or use 'all' to control all plugs."
            
            if self._control_plug(plug_name, state):
                return f"Successfully turned {action} {plug_name}."
            else:
                return f"Error: Failed to turn {action} {plug_name}."
