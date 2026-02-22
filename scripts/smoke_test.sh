#!/usr/bin/env bash
set -euo pipefail

echo "Running unit tests..."
python3 -m unittest discover -s tests -q

echo "OK"
