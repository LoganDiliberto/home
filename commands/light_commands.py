"""Light control command handlers."""

import logging
from typing import TYPE_CHECKING
from core.command import Command
import paho.mqtt.client as mqtt
import json
if TYPE_CHECKING:
    from core.services import ServiceContainer

logger = logging.getLogger(__name__)
MQTT_BROKER = "10.0.0.54"


class TurnOnLightCommand(Command):
    """Command to turn on lights."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn on' and 'light'."""
        return "turn on" in command and "light" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute turn on light command."""
        logger.info("Light control command detected: turn on")
        DEVICE_NAME = "bulb1"
        CONTROL_TOPIC = f"zigbee2mqtt/{DEVICE_NAME}/set"
        payload = {
            "state": "on",
        }
        client = mqtt.Client()
        client.connect(MQTT_BROKER, 1883)
        client.publish(CONTROL_TOPIC, json.dumps(payload))
        client.disconnect()
        return "Turning lights on"
    
    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5


class TurnOffLightCommand(Command):
    """Command to turn off lights."""
    
    def can_handle(self, command: str) -> bool:
        """Check if command contains 'turn off' and 'light'."""
        return "turn off" in command and "light" in command
    
    def execute(self, command: str, services: 'ServiceContainer') -> str:
        """Execute turn off light command."""
        logger.info("Light control command detected: turn off")
        DEVICE_NAME = "bulb1"
        CONTROL_TOPIC = f"zigbee2mqtt/{DEVICE_NAME}/set"
        payload = {
            "state": "off",
        }
        client = mqtt.Client()
        client.connect(MQTT_BROKER, 1883)
        client.publish(CONTROL_TOPIC, json.dumps(payload))
        client.disconnect()
        return "Turning lights off"
    
    def get_priority(self) -> int:
        """Medium priority for light commands."""
        return 5

