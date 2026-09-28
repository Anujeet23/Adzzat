#!/usr/bin/env python3
"""Grades the fast-matmul submission.

Five independent, weighted criteria, run against a single instrumented
call per fixture size (n=8, 16, 32, 64), counting calls to kernel.ops.mul
and checking correctness against this file's own independently computed
reference product:

  1. correctness at n=8                                    20%
  2. correctness at n=64                                     15%
  3. multiplication-count growth ratio 16->32 < 7.5           25%
  4. multiplication-count growth ratio 32->64 < 7.5           25%
  5. absolute multiplication-count bound at n=16               15%
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
MAX_RATIO = 7.5
TOLERANCE = 1e-6


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


def reference_matmul(A, B):
    n = len(A)
    C = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            C[i][j] = sum(A[i][k] * B[k][j] for k in range(n))
    return C


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


def check_correctness(size_name, fixture, result):
    expected = reference_matmul(fixture["A"], fixture["B"])
    n = fixture["n"]
    got = result["C"]
    if len(got) != n or any(len(row) != n for row in got):
        raise ValueError("%s: result has wrong shape" % size_name)
    max_err = max(abs(got[i][j] - expected[i][j]) for i in range(n) for j in range(n))
    if max_err > TOLERANCE:
        raise ValueError("%s: max error %.3g exceeds tolerance %.3g" % (size_name, max_err, TOLERANCE))
    return max_err


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="matmul-eval-"))
    os.chmod(workdir, 0o777)
    _, fixtures_dst = stage(workdir)
    runner = str(workdir / "stage" / "runner.py")

    outcomes = {}
    diagnostics = {}

    fixtures = {}
    results = {}
    run_error = None
    for size_name in ("n8", "n16", "n32", "n64"):
        with open(HERE / "fixtures" / (size_name + ".json"), "r", encoding="utf-8") as f:
            fixtures[size_name] = json.load(f)
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
            err8 = check_correctness("n8", fixtures["n8"], results["n8"])
            outcomes["1"] = 1
            diagnostics["1"] = {"max_error": err8}
        except ValueError as error:
            outcomes["1"] = 0
            diagnostics["1"] = {"error": str(error)}

        try:
            err64 = check_correctness("n64", fixtures["n64"], results["n64"])
            outcomes["2"] = 1
            diagnostics["2"] = {"max_error": err64}
        except ValueError as error:
            outcomes["2"] = 0
            diagnostics["2"] = {"error": str(error)}

        c16 = results["n16"]["mul_count"]
        c32 = results["n32"]["mul_count"]
        c64 = results["n64"]["mul_count"]

        try:
            ratio_16_32 = c32 / c16
            if ratio_16_32 > MAX_RATIO:
                raise ValueError(
                    "multiplication count growth 16->32 is %.3fx (count16=%d, count32=%d), "
                    "exceeding %.2fx -- looks like an O(n^3) algorithm" % (ratio_16_32, c16, c32, MAX_RATIO)
                )
            outcomes["3"] = 1
            diagnostics["3"] = {"ratio_16_32": ratio_16_32, "count16": c16, "count32": c32}
        except ValueError as error:
            outcomes["3"] = 0
            diagnostics["3"] = {"error": str(error)}

        try:
            ratio_32_64 = c64 / c32
            if ratio_32_64 > MAX_RATIO:
                raise ValueError(
                    "multiplication count growth 32->64 is %.3fx (count32=%d, count64=%d), "
                    "exceeding %.2fx -- looks like an O(n^3) algorithm" % (ratio_32_64, c32, c64, MAX_RATIO)
                )
            outcomes["4"] = 1
            diagnostics["4"] = {"ratio_32_64": ratio_32_64, "count32": c32, "count64": c64}
        except ValueError as error:
            outcomes["4"] = 0
            diagnostics["4"] = {"error": str(error)}

        try:
            bound = int(0.7 * 16 ** 3)
            if c16 > bound:
                raise ValueError(
                    "multiplication count at n=16 is %d, exceeding the absolute bound %d" % (c16, bound)
                )
            outcomes["5"] = 1
            diagnostics["5"] = {"count16": c16, "bound": bound}
        except ValueError as error:
            outcomes["5"] = 0
            diagnostics["5"] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "fast-matmul",
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
