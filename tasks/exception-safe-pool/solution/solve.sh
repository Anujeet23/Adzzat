#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/pool
cp /app/repo/pool/__init__.py /app/submission/pool/__init__.py
cp /solution/pool.py /app/submission/pool/pool.py
