#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python -m pip install -e . -q
python -m looplab install-hermes "$@"
