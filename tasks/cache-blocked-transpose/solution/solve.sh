#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/kernel
cp /app/repo/kernel/__init__.py /app/submission/kernel/__init__.py
cp /app/repo/kernel/mem.py /app/submission/kernel/mem.py
cp /solution/transpose.py /app/submission/kernel/transpose.py
