"""XPUB/XSUB broker — central hub for all ZMQ traffic."""

import logging

import zmq
from config.settings import ZMQ_PUBLISH_SIDE, ZMQ_SUBSCRIBE_SIDE

log = logging.getLogger("broker")


def main():
    context = zmq.Context()
    publish_side = context.socket(zmq.XSUB)
    publish_side.bind(ZMQ_PUBLISH_SIDE)
    subscribe_side = context.socket(zmq.XPUB)
    subscribe_side.bind(ZMQ_SUBSCRIBE_SIDE)
    log.info("XSUB on %s, XPUB on %s", ZMQ_PUBLISH_SIDE, ZMQ_SUBSCRIBE_SIDE)
    try:
        zmq.proxy(publish_side, subscribe_side)
    except KeyboardInterrupt:
        pass
    finally:
        publish_side.close()
        subscribe_side.close()
        context.term()


if __name__ == "__main__":
    logging.basicConfig(format="%(name)s: %(message)s", level=logging.INFO)
    main()
