#!/usr/bin/env python3
"""Grades the incremental-topological-sort submission.

Five independent, weighted criteria, each a scripted sequence of
add_node/add_edge/order_check operations run against the actual
submitted DAG object, validating the topological-order property
against a ground-truth node/edge set tracked by the runner itself:

  1. basic correctness, compatible insertion order           15%
  2. longer-cycle detection through intermediate nodes         25%
  3. order consistency when insertion order must be overridden 25%
  4. rejection leaves the graph unchanged, incl. self-loops    20%
  5. a longer mixed sequence, checked at multiple points       15%
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
WEIGHTS = {"1": 15, "2": 25, "3": 25, "4": 20, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 30

FIXTURE_FOR = {
    "1": "basic.json",
    "2": "cycle_detection.json",
    "3": "order_consistency.json",
    "4": "reject_unchanged.json",
    "5": "mixed.json",
}


def check_submission():
    if not (SUBMISSION / "toposort" / "__init__.py").is_file():
        raise ValueError("Submitted toposort package is missing")


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


def run_fixture(runner, fixtures_dst, workdir, tag):
    check_submission()
    ops_path = fixtures_dst / FIXTURE_FOR[tag]
    out_path = workdir / (tag + "-result.json")
    cmd = [PYTHON, runner, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path), "--out", str(out_path)]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode != 0:
        raise ValueError(
            "runner crashed for %s (exit %s): %s" % (tag, proc.returncode, proc.stderr[-2000:])
        )
    with open(out_path, "r", encoding="utf-8") as f:
        result = json.load(f)
    if not result.get("ok"):
        raise ValueError("criterion %s failed: %s" % (tag, result.get("error")))
    return result


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="toposort-eval-"))
    os.chmod(workdir, 0o777)
    _, fixtures_dst = stage(workdir)
    runner = str(workdir / "stage" / "runner.py")

    outcomes = {}
    diagnostics = {}
    for tag in ("1", "2", "3", "4", "5"):
        try:
            diagnostics[tag] = run_fixture(runner, fixtures_dst, workdir, tag)
            outcomes[tag] = 1
        except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
            outcomes[tag] = 0
            diagnostics[tag] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "incremental-topological-sort",
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
