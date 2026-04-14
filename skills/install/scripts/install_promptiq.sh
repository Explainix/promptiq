#!/bin/sh
set -eu

RAW_INSTALLER_URL="https://raw.githubusercontent.com/Explainix/promptiq/main/skills/install/scripts/install_promptiq.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "PromptIQ installation failed: python3 is required." >&2
  exit 1
fi

SCRIPT_DIR=""
case "$0" in
  /*)
    SCRIPT_DIR=$(dirname "$0")
    ;;
  */*)
    SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
    ;;
esac

if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/install_promptiq.py" ]; then
  exec "$PYTHON_BIN" "$SCRIPT_DIR/install_promptiq.py" "$@"
fi

if command -v mktemp >/dev/null 2>&1; then
  TMP_PY=$(mktemp "${TMPDIR:-/tmp}/promptiq-install.XXXXXX.py")
else
  TMP_PY="${TMPDIR:-/tmp}/promptiq-install.py"
fi

cleanup() {
  if [ -n "${TMP_PY:-}" ] && [ -f "$TMP_PY" ]; then
    rm -f "$TMP_PY"
  fi
}

trap cleanup EXIT INT TERM

if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o "$TMP_PY" "$RAW_INSTALLER_URL"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$TMP_PY" "$RAW_INSTALLER_URL"
else
  echo "PromptIQ installation failed: curl or wget is required to download the installer." >&2
  exit 1
fi

exec "$PYTHON_BIN" "$TMP_PY" "$@"
