#!/usr/bin/env bash
set -euo pipefail
set -m

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BACKEND_DIR="${ROOT_DIR}/backend"
PIDS=()

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: python3 or python is required for port detection." >&2
  exit 1
fi

is_port_in_use() {
  local port="$1"
  "${PYTHON_BIN}" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket()
try:
    sock.bind(("127.0.0.1", port))
except OSError:
    sys.exit(0)
finally:
    sock.close()
sys.exit(1)
PY
}

find_available_port() {
  local port="$1"
  while is_port_in_use "${port}"; do
    port=$((port + 1))
  done
  echo "${port}"
}

cleanup() {
  trap - EXIT INT TERM

  for pid in "${PIDS[@]}"; do
    kill -TERM -"${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
  done

  sleep 2

  for pid in "${PIDS[@]}"; do
    kill -KILL -"${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
  done

  wait 2>/dev/null || true
}

wait_for_any_exit() {
  while true; do
    for pid in "${PIDS[@]}"; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        wait "${pid}" 2>/dev/null || true
        return
      fi
    done
    sleep 1
  done
}

trap cleanup EXIT INT TERM

API_PORT="$(find_available_port "${API_PORT:-8080}")"
FLOWER_PORT="$(find_available_port "${FLOWER_PORT:-8555}")"
if [[ "${FLOWER_PORT}" == "${API_PORT}" ]]; then
  FLOWER_PORT="$(find_available_port "$((FLOWER_PORT + 1))")"
fi

echo "Backend API port: ${API_PORT}"
echo "Flower port: ${FLOWER_PORT}"

(
  cd "${FRONTEND_DIR}"
  exec pnpm run dev
) &
PIDS+=("$!")

(
  cd "${BACKEND_DIR}"
  exec uv run fba run --port "${API_PORT}"
) &
PIDS+=("$!")

(
  cd "${BACKEND_DIR}"
  exec uv run fba celery worker
) &
PIDS+=("$!")

(
  cd "${BACKEND_DIR}"
  exec uv run fba celery beat
) &
PIDS+=("$!")

(
  cd "${BACKEND_DIR}"
  exec uv run fba celery flower --port "${FLOWER_PORT}"
) &
PIDS+=("$!")

wait_for_any_exit
