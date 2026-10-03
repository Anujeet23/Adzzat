#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/ratelimit
cp /app/repo/ratelimit/__init__.py /app/submission/ratelimit/__init__.py
cp /solution/ratelimit.py /app/submission/ratelimit/ratelimit.py
