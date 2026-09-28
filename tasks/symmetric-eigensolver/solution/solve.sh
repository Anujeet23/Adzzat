#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/eigensolve
cp /app/repo/eigensolve/__init__.py /app/submission/eigensolve/__init__.py
cp /solution/eigensolve.py /app/submission/eigensolve/eigensolve.py
