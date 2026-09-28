#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/autodiff
cp /app/repo/autodiff/__init__.py /app/submission/autodiff/__init__.py
cp /solution/engine.py /app/submission/autodiff/engine.py
