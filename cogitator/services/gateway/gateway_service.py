"""Bridges ZMQ bus to websocket for explorator.

Data flows one way: ZMQ broker → this gateway → explorator (WebSocket clients).
Each connected WebSocket client receives every message matching GATEWAY_SUBSCRIBE_PREFIXES.
"""

import asyncio
import json
import logging

import zmq
import zmq.asyncio
import websockets

from config.settings import WEBSOCKET_HOST, WEBSOCKET_PORT, ZMQ_SUBSCRIBE_ADDRESS, GATEWAY_SUBSCRIBE_PREFIXES

log = logging.getLogger("gateway")

# All connected WebSocket clients. websocket_handler adds on connect, removes on disconnect.
# zmq_to_websocket iterates this set to broadcast every ZMQ message.
clients: set[websockets.WebSocketServerProtocol] = set()


async def websocket_handler(websocket: websockets.WebSocketServerProtocol):
    """Called once per WebSocket connection. Stays alive for the lifetime of that connection."""
    clients.add(websocket)
    remote = websocket.remote_address
    log.info("client connected from %s", remote)
    try:
        # This loop keeps the connection alive. It yields each message the client sends.
        # Without it, the connection would close immediately.
        async for message in websocket:
            # TODO: handle inbound commands from explorator (e.g. estop, set_velocity)
            # Parse JSON, publish to ZMQ broker for downstream services
            pass
    except websockets.ConnectionClosed:
        pass
    finally:
        clients.discard(websocket)
        log.info("client disconnected %s", remote)


async def zmq_to_websocket(context: zmq.asyncio.Context):
    """Subscribes to ZMQ topics and broadcasts each message to all WebSocket clients."""
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(ZMQ_SUBSCRIBE_ADDRESS)
    for prefix in GATEWAY_SUBSCRIBE_PREFIXES:
        subscriber.subscribe(prefix.encode())
    log.info("subscribed to %s on %s", [p + "*" for p in GATEWAY_SUBSCRIBE_PREFIXES], ZMQ_SUBSCRIBE_ADDRESS)

    try:
        while True:
            # Block until a message arrives from the broker.
            # Each message is two frames: [topic, json_payload]
            frames = await subscriber.recv_multipart()
            if len(frames) != 2:
                log.warning("expected 2-part message, got %d — skipping", len(frames))
                continue
            topic_bytes, payload_bytes = frames
            topic = topic_bytes.decode()

            try:
                data = json.loads(payload_bytes.decode())
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                log.warning("bad payload on %s: %s", topic, error)
                continue

            # Wrap in an envelope so explorator knows which topic this came from
            envelope = json.dumps({"topic": topic, "data": data})

            # Broadcast to all connected clients, collecting any that have disconnected
            dead = set()
            for client in clients:
                try:
                    await client.send(envelope)
                except websockets.ConnectionClosed:
                    dead.add(client)
            clients.difference_update(dead)
    finally:
        subscriber.close()


async def main():
    context = zmq.asyncio.Context()
    # TODO: when inbound commands are needed, create a ZMQ PUB socket here
    # and pass it to websocket_handler via functools.partial

    # websockets.serve starts the WS server and calls websocket_handler for each new connection.
    # zmq_to_websocket runs concurrently, reading from the broker and broadcasting to clients.
    async with websockets.serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT):
        log.info("websocket server on ws://%s:%d", WEBSOCKET_HOST, WEBSOCKET_PORT)
        await zmq_to_websocket(context)


if __name__ == "__main__":
    logging.basicConfig(format="%(name)s: %(message)s", level=logging.INFO)
    asyncio.run(main())
