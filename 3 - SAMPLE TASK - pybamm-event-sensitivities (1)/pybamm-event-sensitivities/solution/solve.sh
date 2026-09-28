#!/bin/bash
set -euo pipefail
cd /app/repo
git apply /solution/feature.patch
cp -R src/pybamm /app/submission/pybamm
