#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/beamsearch
cp /app/repo/beamsearch/__init__.py /app/submission/beamsearch/__init__.py
cp /solution/beamsearch.py /app/submission/beamsearch/beamsearch.py
