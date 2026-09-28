#!/usr/bin/env python3
"""Grades the exception-safe-pool submission.

Five independent, weighted criteria, each run against real exception
propagation through the actual submitted pool object:

  1. basic correctness, no failures injected               15%
  2. caller-exception safety (with/without mark_broken)     30%
  3. exactly-once destroy() for explicitly broken resources 25%
  4. resilience to a resource-factory failure                20%
  5. a longer mixed sequence, checked by final invariants    10%
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
WEIGHTS = {"1": 15, "2": 30, "3": 25, "4": 20, "5": 10}
PYTHON = sys.executable
CALL_TIMEOUT = 30

FIXTURE_FOR = {
    "1": "basic.json",
    "2": "exception_safety.json",
    "3": "broken_resource.json",
    "4": "factory_failure.json",
    "5": "mixed.json",
}


def check_submission():
    if not (SUBMISSION / "pool" / "__init__.py").is_file():
        raise ValueError("Submitted pool package is missing")


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


def run_fixture(runner, ops_path, workdir, tag):
    check_submission()
    out_path = workdir / (tag + "-result.json")
    cmd = [PYTHON, runner, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path), "--out", str(out_path)]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode != 0:
        raise ValueError(
            "runner crashed for %s (exit %s): %s" % (tag, proc.returncode, proc.stderr[-2000:])
        )
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def criterion_1(runner, fixtures_dst, workdir):
    result = run_fixture(runner, fixtures_dst / FIXTURE_FOR["1"], workdir, "basic")
    if not result.get("ok"):
        raise ValueError("basic scenario failed: %s" % result.get("error"))
    if result["live_remaining"]:
        raise ValueError("handles left unreleased at end of basic scenario: %s" % result["live_remaining"])
    return result


def criterion_2(runner, fixtures_dst, workdir):
    result = run_fixture(runner, fixtures_dst / FIXTURE_FOR["2"], workdir, "exception_safety")
    if not result.get("ok"):
        raise ValueError("exception-safety scenario failed: %s" % result.get("error"))
    return result


def criterion_3(runner, fixtures_dst, workdir):
    result = run_fixture(runner, fixtures_dst / FIXTURE_FOR["3"], workdir, "broken_resource")
    if not result.get("ok"):
        raise ValueError("broken-resource scenario failed: %s" % result.get("error"))
    if result["destroyed_total"] != 2:
        raise ValueError(
            "expected exactly 2 destroy() calls in broken-resource scenario, got %d"
            % result["destroyed_total"]
        )
    return result


def criterion_4(runner, fixtures_dst, workdir):
    result = run_fixture(runner, fixtures_dst / FIXTURE_FOR["4"], workdir, "factory_failure")
    if not result.get("ok"):
        raise ValueError("factory-failure scenario failed: %s" % result.get("error"))
    if result["created_total"] != 2:
        raise ValueError(
            "expected exactly 2 resources ever constructed (the failed attempt must not count "
            "and the final acquire must reuse a freed resource), got %d" % result["created_total"]
        )
    return result


def criterion_5(runner, fixtures_dst, workdir):
    result = run_fixture(runner, fixtures_dst / FIXTURE_FOR["5"], workdir, "mixed")
    if not result.get("ok"):
        raise ValueError("mixed scenario failed: %s" % result.get("error"))
    if result["final_outstanding"] != 0:
        raise ValueError("mixed scenario ended with outstanding=%d, expected 0" % result["final_outstanding"])
    if result["destroyed_total"] != 2:
        raise ValueError(
            "expected exactly 2 destroy() calls in mixed scenario, got %d" % result["destroyed_total"]
        )
    return result


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="pool-eval-"))
    os.chmod(workdir, 0o777)
    _, fixtures_dst = stage(workdir)
    runner = str(workdir / "stage" / "runner.py")

    outcomes = {}
    diagnostics = {}
    for number, fn in (
        ("1", criterion_1),
        ("2", criterion_2),
        ("3", criterion_3),
        ("4", criterion_4),
        ("5", criterion_5),
    ):
        try:
            diagnostics[number] = fn(runner, fixtures_dst, workdir)
            outcomes[number] = 1
        except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
            outcomes[number] = 0
            diagnostics[number] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "exception-safe-pool",
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
