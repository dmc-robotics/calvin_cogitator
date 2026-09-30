# Calvin Serial Protocol

Communication between Instinctus (Teensy 4.1) and Cogitator (Jetson Orin Nano).

## Physical Layer

- **Connection**: Serial (Teensy Serial1 <-> Jetson UART)
- **Baud rate**: 1,000,000
- **Framing**: Newline-delimited JSON (`\n` terminated)
- **Encoding**: ASCII

## Message Format

Every message is a single JSON object on one line. All messages include:

| Field  | Type   | Description                        |
|--------|--------|------------------------------------|
| `type` | string | Message type identifier            |
| `ms`   | uint32 | Sender's timestamp (millis)        |

Additional fields depend on the message type.

---

## Teensy -> Jetson Messages

### `telemetry` — Balance and motor state

Sent at 50 Hz.

| Field       | Type  | Unit      | Description                  |
|-------------|-------|-----------|------------------------------|
| `tilt`      | float | degrees   | Current tilt angle           |
| `tiltRate`  | float | deg/sec   | Rate of tilt change          |
| `targetVel` | float | m/s       | Commanded velocity           |
| `motorL`    | float | rad/s     | Left motor velocity          |
| `motorR`    | float | rad/s     | Right motor velocity         |
| `loopCount` | uint32|           | Balance ISR iteration count  |

```json
{"type":"telemetry","ms":12345,"tilt":1.23,"tiltRate":-0.45,"targetVel":0.0,"motorL":0.0,"motorR":0.0,"loopCount":12345}
```

### `event` — State changes and alerts

Sent when the event occurs (not periodic).

| Field   | Type   | Description                            |
|---------|--------|----------------------------------------|
| `event` | string | Event identifier (see table below)     |
| `data`  | object | Optional, event-specific payload       |

Events:

| Event ID        | Meaning                          | Data fields        |
|-----------------|----------------------------------|--------------------|
| `estop`         | Emergency stop triggered         | `reason` (string)  |
| `estop_clear`   | Emergency stop cleared           |                    |
| `fault`         | Fault detected                   | `flags` (uint8)    |
| `fault_clear`   | Fault cleared                    |                    |
| `mode_change`   | Operating mode changed           | `mode` (string)    |

```json
{"type":"event","ms":12345,"event":"estop","data":{"reason":"tilt_limit"}}
```

### `log` — Debug and diagnostic messages

Sent as needed. Not time-critical.

| Field   | Type   | Description                              |
|---------|--------|------------------------------------------|
| `level` | string | `DEBUG`, `INFO`, `WARN`, `ERROR`         |
| `msg`   | string | Human-readable message (escaped JSON)    |

```json
{"type":"log","ms":12345,"level":"INFO","msg":"Instinctus awakens."}
```

### `ack` — Command acknowledgement

Sent in response to a received command.

| Field  | Type   | Description                               |
|--------|--------|-------------------------------------------|
| `cmd`  | string | The command type being acknowledged       |
| `ok`   | bool   | Whether the command was accepted          |
| `msg`  | string | Optional, error reason if `ok` is false   |

```json
{"type":"ack","ms":12345,"cmd":"set_velocity","ok":true}
```

---

## Jetson -> Teensy Messages

### `command` — Control commands

| Field    | Type   | Description                            |
|----------|--------|----------------------------------------|
| `cmd`    | string | Command identifier (see table below)   |
| `data`   | object | Command-specific payload               |

Commands:

| Command ID      | Description                | Data fields                 |
|-----------------|----------------------------|-----------------------------|
| `set_velocity`  | Set target velocity        | `velocity` (float, m/s)    |
| `set_mode`      | Change operating mode      | `mode` (string)            |
| `estop`         | Trigger emergency stop     |                             |
| `estop_clear`   | Clear emergency stop       |                             |

```json
{"type":"command","ms":98765,"cmd":"set_velocity","data":{"velocity":0.5}}
```

### `config` — Runtime configuration changes

| Field   | Type   | Description                             |
|---------|--------|-----------------------------------------|
| `param` | string | Parameter name                          |
| `value` | varies | New value                               |

```json
{"type":"config","ms":98765,"param":"pid_kp","value":1.5}
```

### `ping` — Keepalive / latency check

No additional fields. Teensy responds with an `ack`.

```json
{"type":"ping","ms":98765}
```

---

## Error Handling

- **Malformed JSON**: Receiver logs a warning and discards the line.
- **Unknown message type**: Receiver logs a warning and ignores the message.
- **Serial disconnect**: Cogitator retries connection every 2 seconds. Instinctus continues operating independently (balance loop is unaffected).
- **Command timeout**: If Cogitator sends a command and receives no `ack` within 500ms, it may retry or log an error. Instinctus is not required to guarantee delivery.

## Notes

- The Teensy's balance loop runs in a hardware ISR and is never affected by serial communication.
- All serial I/O on the Teensy happens in `loop()` — it is best-effort and non-blocking.
- Message field values use JSON-escaped strings where needed (quotes, backslashes, newlines).
