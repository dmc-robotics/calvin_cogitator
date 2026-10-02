# Calvin Cogitator

Big picture (systems, wiring, control architecture, working rules): see `../CLAUDE.md`.

High-level services on the Jetson Orin Nano (Python). **Today:** a message pipeline: Teensy serial → ZMQ bus → WebSocket gateway → explorator. **Later:** vision (OAK-D Pro W), navigation/planning, and an LLM interface, sending velocity/heading commands down to the Teensy at 20–50 Hz.

## Layout

```
calvin_cogitator/
├── PROTOCOL.md               Teensy ↔ Jetson serial protocol (the source of truth)
├── DOCKER.md                 Jetson container cheat sheet (dustynv/pytorch image, volumes, day-to-day commands)
├── cogitator.plan.md         early bring-up plan (historical; mentions the old ICM20948 IMU and unbuilt topics)
├── cogitator/
│   ├── run.sh                dev launcher: broker + serial (or --dummy) + gateway as background processes
│   ├── broker.py             ZMQ XPUB/XSUB proxy (5550 publish side, 5551 subscribe side)
│   ├── test.html             WebSocket gateway test page
│   ├── config/settings.py    addresses, ports, serial settings, type→topic map (env-overridable, COGITATOR_*)
│   └── services/
│       ├── serial/serial_service.py     reads newline JSON from the Teensy, publishes to ZMQ
│       ├── gateway/gateway_service.py   forwards ZMQ topics to WebSocket clients on :5560
│       └── dummy/dummy_service.py       fake Teensy messages for development
└── systemd/                  unit files + install.sh for running the services on the Jetson (see SYSTEMD.md)
```

## How messages flow

- All ZMQ messages are multipart frames `[topic, json_payload]`.
- The serial service maps the Teensy's `type` field to a ZMQ topic via `MESSAGE_TYPE_TO_TOPIC` in `config/settings.py` (the single source of truth for routing; e.g. `telemetry` → `sensor.telemetry`, `log` → `instinctus.log`).
- Message fields are defined in `PROTOCOL.md`.
- The gateway forwards topics starting with `sensor.` or `instinctus.` (`GATEWAY_SUBSCRIBE_PREFIXES`) to explorator as `{"topic", "data"}` WebSocket messages.
- **Inbound commands (explorator → Teensy) aren't implemented:** the gateway ignores incoming messages (TODOs in `gateway_service.py`).

## Running

- Dev (on the Mac or the Jetson): `cd cogitator && ./run.sh` (real serial) or `./run.sh --dummy` (fake data; this is how explorator is tested without hardware).
- Production on the Jetson: the systemd units in `systemd/`.
- Settings are overridable with `COGITATOR_*` environment variables (see `config/settings.py`).

## Serial link to the Teensy

The link is a **UART**: Teensy `Serial1` (pins 0/1) ↔ a UART on the Jetson's 40-pin header, 3.3 V logic, shared ground, 1,000,000 baud. **To do:** `SERIAL_DEVICE` in `config/settings.py` still defaults to `/dev/ttyACM0` (USB serial, from an earlier plan). Change it to the header UART's device (a `/dev/ttyTHS*` node; confirm which on the Jetson), make sure no serial console or getty is using that port, pass the device into the Docker container (`--device`), and document that host setup here once it works.

## Code style

No abbreviations in variable, constant, function or environment variable names (`publisher`, not `pub`; `ZMQ_PUBLISH_ADDRESS`, not `ZMQ_PUB_ADDR`; `COGITATOR_`, not `COG_`).
