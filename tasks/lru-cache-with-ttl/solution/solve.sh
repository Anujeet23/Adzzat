#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/cache
cp /app/repo/cache/__init__.py /app/submission/cache/__init__.py
cp /solution/cache.py /app/submission/cache/cache.py
