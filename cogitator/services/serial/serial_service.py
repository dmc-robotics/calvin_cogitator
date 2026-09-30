"""Reads Teensy UART, publishes messages to ZMQ bus.

Data flows one way: Teensy (Serial) → this service → ZMQ broker.
The Teensy sends newline-delimited JSON. Each line's "type" field is mapped
to a ZMQ topic via MESSAGE_TYPE_TO_TOPIC (defined in settings.py), then
published as a two-frame message: [topic, json_payload].
"""

import json
import logging
import time

import serial
import zmq

from config.settings import (
    SERIAL_DEVICE,
    SERIAL_BAUD_RATE,
    SERIAL_RECONNECT_DELAY,
    ZMQ_PUBLISH_ADDRESS,
    MESSAGE_TYPE_TO_TOPIC,
)

log = logging.getLogger("serial")


def open_serial(device: str, baud_rate: int) -> serial.Serial:
    """Try to open the serial port, retrying forever until it succeeds.
    This handles the case where the Teensy isn't plugged in yet at boot."""
    while True:
        try:
            # timeout=0.1 means readline() will return after 100ms even if
            # no newline arrived — prevents blocking forever on a quiet port
            port = serial.Serial(device, baud_rate, timeout=0.1)
            log.info("opened %s @ %d", device, baud_rate)
            return port
        except serial.SerialException as error:
            log.warning("%s — retrying in %ss", error, SERIAL_RECONNECT_DELAY)
            time.sleep(SERIAL_RECONNECT_DELAY)


def main():
    # Create a ZMQ PUB socket and connect to the broker's XSUB side.
    # Messages published here flow through the broker to all subscribers
    # (e.g. the gateway service, which forwards them to explorator).
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.connect(ZMQ_PUBLISH_ADDRESS)
    log.info("publishing to %s", ZMQ_PUBLISH_ADDRESS)

    port = open_serial(SERIAL_DEVICE, SERIAL_BAUD_RATE)

    try:
        while True:
            # Read one line from the Teensy. Returns empty bytes on timeout.
            try:
                raw = port.readline()
            except serial.SerialException as error:
                # USB disconnect, device removed, etc. — reconnect and retry.
                log.warning("lost connection — %s", error)
                port.close()
                port = open_serial(SERIAL_DEVICE, SERIAL_BAUD_RATE)
                continue

            # Timeout with no data — loop back and try again
            if not raw:
                continue

            # Decode bytes to string. errors="replace" avoids crashing on
            # garbled bytes (e.g. during a partial power-on transmission).
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            # Parse the JSON. Malformed lines are logged and dropped.
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                log.warning("bad json: %r", line)
                continue

            # Look up the ZMQ topic for this message type.
            # Unknown types are logged and dropped — this means if instinctus
            # adds a new message type, it needs a matching entry in settings.py.
            message_type = message.get("type")
            topic = MESSAGE_TYPE_TO_TOPIC.get(message_type)
            if topic is None:
                log.warning("unknown type: %s", message_type)
                continue

            # Publish to the broker as [topic, json_payload]
            publisher.send_multipart([topic.encode(), json.dumps(message).encode()])
    except KeyboardInterrupt:
        pass
    finally:
        port.close()
        publisher.close()
        context.term()


if __name__ == "__main__":
    logging.basicConfig(format="%(name)s: %(message)s", level=logging.INFO)
    main()
