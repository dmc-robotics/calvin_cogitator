import os

# ZMQ broker
ZMQ_PUBLISH_SIDE = os.environ.get("COGITATOR_ZMQ_PUBLISH_SIDE", "tcp://*:5550")       # services connect here to publish
ZMQ_SUBSCRIBE_SIDE = os.environ.get("COGITATOR_ZMQ_SUBSCRIBE_SIDE", "tcp://*:5551")   # subscribers connect here
ZMQ_PUBLISH_ADDRESS = os.environ.get("COGITATOR_ZMQ_PUBLISH_ADDRESS", "tcp://localhost:5550")
ZMQ_SUBSCRIBE_ADDRESS = os.environ.get("COGITATOR_ZMQ_SUBSCRIBE_ADDRESS", "tcp://localhost:5551")

# Websocket gateway
WEBSOCKET_HOST = os.environ.get("COGITATOR_WEBSOCKET_HOST", "0.0.0.0")
WEBSOCKET_PORT = int(os.environ.get("COGITATOR_WEBSOCKET_PORT", "5560"))

# Serial
SERIAL_DEVICE = os.environ.get("COGITATOR_SERIAL_DEVICE", "/dev/ttyACM0")
SERIAL_BAUD_RATE = int(os.environ.get("COGITATOR_SERIAL_BAUD_RATE", "1000000"))
SERIAL_RECONNECT_DELAY = float(os.environ.get("COGITATOR_SERIAL_RECONNECT_DELAY", "2.0"))

# Map Teensy message "type" field → ZMQ topic.
# This is the single source of truth for all topic routing.
MESSAGE_TYPE_TO_TOPIC = {
    "telemetry": "sensor.telemetry",
    "log":       "instinctus.log",
    "event":     "instinctus.event",
    "ack":       "instinctus.ack",
}

# Topic prefixes the gateway forwards to explorator
GATEWAY_SUBSCRIBE_PREFIXES = ["sensor.", "instinctus."]
