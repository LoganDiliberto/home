# Install paho-mqtt: pip install paho-mqtt
#https://www.zigbee2mqtt.io/guide/getting-started/#onboarding
#https://www.zigbee2mqtt.io/devices/046677592530.html
#https://www.zigbee2mqtt.io/devices/4200-C.html
# https://www.zigbee2mqtt.io/devices/25EB-1_30-TYZ.html
import paho.mqtt.client as mqtt
import json

# --- MQTT Client Setup ---
client = mqtt.Client("HuePythonClient") # Unique Client ID

# Define callback functions (optional but recommended)
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to topics if you want to receive state changes
    # client.subscribe("hue2mqtt/light/1") # Example: Subscribe to light 1's state

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")

client.on_connect = on_connect
client.on_message = on_message

# --- Connect to MQTT Broker ---
# Replace with your broker's address and port (e.g., a local Mosquitto broker)
broker_address = "localhost"
broker_port = 1883
client.connect(broker_address, broker_port, 60)

# --- Start the loop (non-blocking) ---
client.loop_start()

# --- Publish Commands ---
light_id = "1" # Example Hue Light ID
set_topic = f"hue2mqtt/light/{light_id}/set"

# Turn light on
payload_on = {"on": True}
client.publish(set_topic, json.dumps(payload_on), qos=1)
print(f"Published: {payload_on} to {set_topic}")

# Wait a moment
import time
time.sleep(2)

# Turn light off
payload_off = {"on": False}
client.publish(set_topic, json.dumps(payload_off), qos=1)
print(f"Published: {payload_off} to {set_topic}")

# --- Stop loop ---
client.loop_stop()
client.disconnect()
