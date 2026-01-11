# Install paho-mqtt: pip install paho-mqtt
#https://www.zigbee2mqtt.io/guide/getting-started/#onboarding
#https://www.zigbee2mqtt.io/devices/046677592530.html
#https://www.zigbee2mqtt.io/devices/4200-C.html
# https://www.zigbee2mqtt.io/devices/25EB-1_30-TYZ.html
import paho.mqtt.client as mqtt
import json

# # Replace with your settings
MQTT_BROKER = "10.0.0.54"

DEVICE_NAME = "bulb1"   # or "starter_bulb" if you renamed it
CONTROL_TOPIC = f"zigbee2mqtt/{DEVICE_NAME}/set"
payload = {
    "state": "off", # Current name or IEEE address
}
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883)
client.publish(CONTROL_TOPIC, json.dumps(payload))
client.disconnect()
