#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/kernel
cp /app/repo/kernel/__init__.py /app/submission/kernel/__init__.py
cp /app/repo/kernel/ops.py /app/submission/kernel/ops.py
cp /solution/matmul.py /app/submission/kernel/matmul.py
