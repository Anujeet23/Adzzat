#!/bin/bash
set -euo pipefail
mkdir -p /app/submission/rootfind
cp /app/repo/rootfind/__init__.py /app/submission/rootfind/__init__.py
cp /solution/rootfind.py /app/submission/rootfind/rootfind.py
