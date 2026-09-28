#!/usr/bin/env python3
"""Grades the cache-blocked-transpose submission.

Five independent, weighted criteria, each run against a single
instrumented call per fixture size (n=16, 32, 64, 128), using the
submission's own kernel.mem simulated cache for miss counting, and
checking correctness against this file's own independent reference:

  1. correctness at n=16 (fits entirely in the simulated cache)   20%
  2. correctness at n=64 (does not fit)                            15%
  3. miss-count growth ratio 32->64 < 6.0                           25%
  4. absolute miss-count bound at n=64                               25%
  5. absolute miss-count bound at n=128                              15%
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run  # noqa: E402

HERE = Path(__file__).resolve().parent
LOGS = Path(os.environ.get("KV_GRADE_LOGS_DIR", "/logs/verifier"))
SUBMISSION = Path(os.environ.get("KV_GRADE_SUBMISSION_DIR", "/app/submission"))
WEIGHTS = {"1": 20, "2": 15, "3": 25, "4": 25, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 90
MAX_RATIO = 6.0
BOUND_64 = 2000
BOUND_128 = 8000


def check_submission():
    if not (SUBMISSION / "kernel" / "__init__.py").is_file():
        raise ValueError("Submitted kernel package is missing")


def stage(workdir):
    stage_dir = workdir / "stage"
    stage_dir.mkdir(mode=0o755)
    for name in ("runner.py", "helpers.py"):
        dst = stage_dir / name
        shutil.copyfile(HERE / name, dst)
        os.chmod(dst, 0o644)
    fixtures_dst = stage_dir / "fixtures"
    fixtures_dst.mkdir(mode=0o755)
    for fixture in (HERE / "fixtures").glob("*.json"):
        dst = fixtures_dst / fixture.name
        shutil.copyfile(fixture, dst)
        os.chmod(dst, 0o644)
    return stage_dir, fixtures_dst


def reference_transpose(n):
    src = [float(i) for i in range(n * n)]
    dst = [0.0] * (n * n)
    for i in range(n):
        for j in range(n):
            dst[j * n + i] = src[i * n + j]
    return dst


def run_fixture(runner, fixtures_dst, workdir, size_name):
    check_submission()
    ops_path = fixtures_dst / (size_name + ".json")
    out_path = workdir / (size_name + "-result.json")
    cmd = [PYTHON, runner, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path), "--out", str(out_path)]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode != 0:
        raise ValueError(
            "runner crashed for %s (exit %s): %s" % (size_name, proc.returncode, proc.stderr[-2000:])
        )
    with open(out_path, "r", encoding="utf-8") as f:
        result = json.load(f)
    if not result.get("ok"):
        raise ValueError("runner failed for %s: %s" % (size_name, result.get("error")))
    return result


def check_correctness(size_name, n, result):
    expected = reference_transpose(n)
    got = result["out"]
    if got != expected:
        bad = next(i for i in range(len(expected)) if got[i] != expected[i])
        raise ValueError(
            "%s: output mismatch at flat index %d: got %r, expected %r" % (size_name, bad, got[bad], expected[bad])
        )


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="transpose-eval-"))
    os.chmod(workdir, 0o777)
    _, fixtures_dst = stage(workdir)
    runner = str(workdir / "stage" / "runner.py")

    outcomes = {}
    diagnostics = {}

    results = {}
    run_error = None
    for size_name in ("n16", "n32", "n64", "n128"):
        try:
            results[size_name] = run_fixture(runner, fixtures_dst, workdir, size_name)
        except ValueError as error:
            run_error = str(error)
            results[size_name] = None

    def fail_all(error):
        for k in ("1", "2", "3", "4", "5"):
            outcomes[k] = 0
            diagnostics[k] = {"error": error}

    if run_error:
        fail_all(run_error)
    else:
        try:
            check_correctness("n16", 16, results["n16"])
            outcomes["1"] = 1
            diagnostics["1"] = {"ok": True}
        except ValueError as error:
            outcomes["1"] = 0
            diagnostics["1"] = {"error": str(error)}

        try:
            check_correctness("n64", 64, results["n64"])
            outcomes["2"] = 1
            diagnostics["2"] = {"ok": True}
        except ValueError as error:
            outcomes["2"] = 0
            diagnostics["2"] = {"error": str(error)}

        m32 = results["n32"]["misses"]
        m64 = results["n64"]["misses"]
        m128 = results["n128"]["misses"]

        try:
            ratio = m64 / m32
            if ratio > MAX_RATIO:
                raise ValueError(
                    "miss-count growth 32->64 is %.3fx (misses32=%d, misses64=%d), exceeding %.2fx"
                    % (ratio, m32, m64, MAX_RATIO)
                )
            outcomes["3"] = 1
            diagnostics["3"] = {"ratio_32_64": ratio, "misses32": m32, "misses64": m64}
        except ValueError as error:
            outcomes["3"] = 0
            diagnostics["3"] = {"error": str(error)}

        try:
            if m64 > BOUND_64:
                raise ValueError("misses at n=64 is %d, exceeding bound %d" % (m64, BOUND_64))
            outcomes["4"] = 1
            diagnostics["4"] = {"misses64": m64, "bound": BOUND_64}
        except ValueError as error:
            outcomes["4"] = 0
            diagnostics["4"] = {"error": str(error)}

        try:
            if m128 > BOUND_128:
                raise ValueError("misses at n=128 is %d, exceeding bound %d" % (m128, BOUND_128))
            outcomes["5"] = 1
            diagnostics["5"] = {"misses128": m128, "bound": BOUND_128}
        except ValueError as error:
            outcomes["5"] = 0
            diagnostics["5"] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "cache-blocked-transpose",
        "reward": reward,
        "weighted_score": sum(WEIGHTS[k] * outcomes[k] for k in outcomes) / 100,
        "per_criterion": outcomes,
        "full_pass": bool(reward),
        "weights": WEIGHTS,
        "diagnostics": diagnostics,
    }
    (LOGS / "criteria.json").write_text(json.dumps(report, indent=2, allow_nan=False))
    (LOGS / "reward.txt").write_text(str(reward))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
