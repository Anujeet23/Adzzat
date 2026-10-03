#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/ringbuffer
cp /app/repo/ringbuffer/__init__.py /app/submission/ringbuffer/__init__.py
cp /solution/ringbuffer.py /app/submission/ringbuffer/ringbuffer.py
