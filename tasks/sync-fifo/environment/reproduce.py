#!/usr/bin/env python3
"""Runs a small cocotb simulation against /app/repo/fifo.v and prints its
output, which demonstrates the current implementation losing a write
issued during a simultaneous full+write+read cycle."""
import subprocess
import sys

if __name__ == "__main__":
    proc = subprocess.run(["make"], cwd="/app", capture_output=True, text=True)
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)
