# Calvin Cogitator - Project Instructions

## System Overview

**Calvin Cogitator** is the high-level intelligence system for Calvin, a self-balancing robot. Running on a Jetson Orin Nano, it provides advanced AI capabilities including object recognition, motion planning, video/audio streaming, and LLM-based decision making.

**Calvin's Three-System Architecture:**
- **instinctus** - Low-level reflexes and motor control- `/Users/damoncali/code/robotics/calvin/calvin_instinctus/CLAUDE.md`
- **cogitator** (THIS SYSTEM) - High-level thinking and AI (Jetson Orin Nano)
- **explorator** - Human monitoring interface (native macOS app) - `/Users/damoncali/code/robotics/calvin/calvin_explorator/CLAUDE.md`

**Integration:**
- Receives status from instinctus M7 core via serial
- Sends commands to instinctus M7 core via serial
- Streams telemetry to explorator via network
- Receives user commands from explorator via network

## Jetson Orin Nano Platform

**Hardware:**
- CPU: 6-core ARM Cortex-A78AE @ 1.5 GHz
- GPU: 1024-core NVIDIA Ampere with 32 Tensor Cores
- Memory: 8GB LPDDR5
- Storage: microSD + NVMe SSD (recommended)
- USB: 4x USB 3.2, 1x USB-C
- Network: Gigabit Ethernet, M.2 WiFi
- GPIO: 40-pin header (UART, I2C, SPI, GPIO)

**Peripherals:**
- OAK-D Pro W camera (stereo depth, object detection, built-in IMU)
- USB or GPIO UART connection to Teensy 4.1

## Responsibilities (THIS SYSTEM)

**High-Level Intelligence:**
- Object recognition and tracking
- Motion planning and path finding
- Visual SLAM and navigation
- Sensor fusion from multiple sources
- LLM interface for natural language control
- High-level decision making and goal planning

**Communication Hub:**
- Serial communication with instinctus
- Network communication with explorator
- Video/audio streaming to explorator
- Telemetry aggregation and forwarding

## Project Structure

```
calvin_cogitator/
├── requirements.txt          # pyzmq, pyserial, websockets
├── cogitator/
│   ├── run.sh                # Process launcher (--dummy flag for fake data)
│   ├── broker.py             # ZMQ XPUB/XSUB broker (central message hub)
│   ├── test.html             # WebSocket gateway test page
│   ├── config/
│   │   └── settings.py       # ZMQ addresses, WS config, serial config, topic names
│   └── services/
│       ├── gateway/
│       │   └── gateway_service.py   # Bridges ZMQ bus ↔ WebSocket (for explorator)
│       ├── serial/
│       │   └── serial_service.py    # Reads Teensy UART, publishes to ZMQ bus
│       └── dummy/
│           └── dummy_service.py     # Generates fake Teensy data for testing
└── systemd/
    ├── install.sh                   # Installs and enables all systemd services
    ├── SYSTEMD.md                   # Systemd setup and usage notes
    ├── cogitator-broker.service
    ├── cogitator-gateway.service
    ├── cogitator-serial.service
    └── cogitator-dummy.service
```

## Architecture

### Services
- **ZMQ Broker**: XPUB/XSUB proxy on ports 5550/5551 — all services publish/subscribe through it
- **Gateway Service**: Bridges ZMQ subscriptions to WebSocket on port 5560 for explorator
- **Serial Service**: Reads JSON messages from Teensy over UART, maps message types to ZMQ topics

### Development
- **Dummy Service**: Replaces serial service with synthetic data for development/testing
- **run.sh**: Launches broker + gateway + serial (or `--dummy`) as background processes for development

### Production
- Uses `systemd` services in `/systemd` to manage services on the Jetson


## Message Format

All messages are ZMQ multipart frames: `[topic, json_payload]`.

### Teensy Messages (Teensy → serial service → ZMQ bus)
Teensy sends newline-delimited JSON (see PROTOCOL.md). Serial service maps `type` field to a ZMQ topic and republishes.

| Type        | ZMQ Topic            | Fields                                                              |
|-------------|----------------------|---------------------------------------------------------------------|
| `telemetry` | `sensor.telemetry`   | `ms`, `tilt` (deg), `tiltRate` (deg/s), `targetVel` (m/s), `motorL`, `motorR` (rad/s), `loopCount` |
| `log`       | `instinctus.log`     | `ms`, `level` (DEBUG/INFO/WARN/ERROR), `msg`                       |
| `event`     | `instinctus.event`   | `ms`, `event` (string), `data` (optional object)                   |
| `ack`       | `instinctus.ack`     | `ms`, `cmd` (string), `ok` (bool), `msg` (optional)                |

```json
{"type":"telemetry","ms":12345,"tilt":1.23,"tiltRate":-0.45,"targetVel":0.0,"motorL":0.0,"motorR":0.0,"loopCount":12345}
{"type":"log","ms":12345,"level":"INFO","msg":"Instinctus awakens."}
{"type":"event","ms":12345,"event":"estop","data":{"reason":"tilt_limit"}}
{"type":"ack","ms":12345,"cmd":"set_velocity","ok":true}
```

### Gateway Forwarding
The gateway forwards topics with prefixes `sensor.` and `instinctus.` to explorator via WebSocket.

## Code Style

- Avoid abbreviations in variable, constant, function, and environment variable names. Prefer clarity over brevity (e.g. `publisher` not `pub`, `context` not `ctx`, `ZMQ_PUBLISH_ADDRESS` not `ZMQ_PUB_ADDR`, `COGITATOR_` not `COG_`).
