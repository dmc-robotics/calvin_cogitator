"""Generates fake Teensy data and publishes to ZMQ bus — drop-in replacement for serial service."""

import json
import logging
import math
import random
import time

import zmq

from config.settings import ZMQ_PUBLISH_ADDRESS, MESSAGE_TYPE_TO_TOPIC

log = logging.getLogger("dummy")

PUBLISH_HERTZ = 50  # match real telemetry rate


def generate_telemetry(elapsed: float, loop_count: int) -> dict:
    """Simulate balance telemetry per PROTOCOL.md."""
    return {
        "type": "telemetry",
        "ms": int(elapsed * 1000) % (2**32),
        "tilt": 0.5 * math.sin(elapsed * 2) + random.gauss(0, 0.1),
        "tiltRate": 0.3 * math.cos(elapsed * 3) + random.gauss(0, 0.05),
        "targetVel": 0.0,
        "motorL": 0.0,
        "motorR": 0.0,
        "loopCount": loop_count,
    }


def generate_log(elapsed: float) -> dict:
    """Simulate periodic log messages per PROTOCOL.md."""
    return {
        "type": "log",
        "ms": int(elapsed * 1000) % (2**32),
        "level": "INFO",
        "msg": "heartbeat",
    }


def main():
    context = zmq.Context()

    publisher = context.socket(zmq.PUB)
    publisher.connect(ZMQ_PUBLISH_ADDRESS)

    log.info("publishing to %s at ~%d Hz", ZMQ_PUBLISH_ADDRESS, PUBLISH_HERTZ)

    interval = 1.0 / PUBLISH_HERTZ
    tick = 0
    loop_count = 0
    next_tick = time.monotonic()

    # Send startup log message
    startup = {"type": "log", "ms": 0, "level": "INFO", "msg": "Instinctus awakens. (dummy)"}
    publisher.send_multipart([MESSAGE_TYPE_TO_TOPIC["log"].encode(), json.dumps(startup).encode()])

    try:
        while True:
            elapsed = time.monotonic()
            loop_count += 20  # simulate 1kHz ISR running 20x per 50Hz tick

            # Telemetry every tick (50 Hz)
            message = generate_telemetry(elapsed, loop_count)
            topic = MESSAGE_TYPE_TO_TOPIC[message["type"]]
            publisher.send_multipart([topic.encode(), json.dumps(message).encode()])

            # Log heartbeat every 50 ticks (~1 Hz)
            if tick % 50 == 0:
                message = generate_log(elapsed)
                topic = MESSAGE_TYPE_TO_TOPIC[message["type"]]
                publisher.send_multipart([topic.encode(), json.dumps(message).encode()])

            tick += 1
            next_tick += interval
            time.sleep(max(0, next_tick - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        publisher.close()
        context.term()


if __name__ == "__main__":
    logging.basicConfig(format="%(name)s: %(message)s", level=logging.INFO)
    main()
