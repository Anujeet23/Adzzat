#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/bpe
cp /app/repo/bpe/__init__.py /app/submission/bpe/__init__.py
cp /solution/bpe.py /app/submission/bpe/bpe.py
