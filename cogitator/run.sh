#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PIDS=()

cleanup() {
    echo "shutting down…"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait
    echo "done."
}
trap cleanup INT TERM

cd "$DIR"
export PYTHONPATH="$DIR"

python3 broker.py &
PIDS+=($!)
sleep 0.5  # let broker bind

if [[ "${1:-}" == "--dummy" ]]; then
    echo "using dummy sensor data"
    python3 services/dummy/dummy_service.py &
    PIDS+=($!)
else
    python3 services/serial/serial_service.py &
    PIDS+=($!)
fi

python3 services/gateway/gateway_service.py &
PIDS+=($!)

echo "cogitator running (pids: ${PIDS[*]})"
wait
