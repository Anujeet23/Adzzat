#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/kvstore
cp /app/repo/kvstore/__init__.py /app/submission/kvstore/__init__.py
cp /app/repo/kvstore/iolayer.py /app/submission/kvstore/iolayer.py
cp /solution/store.py /app/submission/kvstore/store.py
