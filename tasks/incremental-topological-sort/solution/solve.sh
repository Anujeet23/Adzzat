#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/toposort
cp /app/repo/toposort/__init__.py /app/submission/toposort/__init__.py
cp /solution/toposort.py /app/submission/toposort/toposort.py
