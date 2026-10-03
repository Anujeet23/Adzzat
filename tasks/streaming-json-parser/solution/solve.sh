#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/jsonstream
cp /app/repo/jsonstream/__init__.py /app/submission/jsonstream/__init__.py
cp /solution/jsonstream.py /app/submission/jsonstream/jsonstream.py
