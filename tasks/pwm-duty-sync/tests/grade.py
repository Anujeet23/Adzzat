#!/usr/bin/env python3
"""Grades the pwm-duty-sync submission.

Five independent, weighted criteria, one per cocotb test function in
test_pwm_gen.py, each comparing the compiled Verilog module's
cycle-by-cycle behavior in Icarus Verilog against an independent Python
reference model:

  1. test_steady_state                    15%
  2. test_mid_period_no_glitch            30%
  3. test_clean_boundary_application      25%
  4. test_multiple_writes_last_wins       15%
  5. test_mixed_random                    15%
"""
import json
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run  # noqa: E402

HERE = Path(__file__).resolve().parent
LOGS = Path(os.environ.get("KV_GRADE_LOGS_DIR", "/logs/verifier"))
SUBMISSION = Path(os.environ.get("KV_GRADE_SUBMISSION_DIR", "/app/submission"))
CALL_TIMEOUT = 180

WEIGHTS = {"1": 15, "2": 30, "3": 25, "4": 15, "5": 15}
TEST_FOR = {
    "1": "test_steady_state",
    "2": "test_mid_period_no_glitch",
    "3": "test_clean_boundary_application",
    "4": "test_multiple_writes_last_wins",
    "5": "test_mixed_random",
}


def check_submission():
    if not (SUBMISSION / "pwm_gen.v").is_file():
        raise ValueError("Submitted pwm_gen.v is missing")


def stage(workdir):
    for name in ("Makefile", "test_pwm_gen.py"):
        dst = workdir / name
        shutil.copyfile(HERE / name, dst)
        os.chmod(dst, 0o644)
    os.chmod(workdir, 0o777)


def run_simulation(workdir):
    check_submission()
    proc = run(["make"], timeout=CALL_TIMEOUT, cwd=str(workdir))
    results_path = workdir / "results.xml"
    return proc, results_path


def parse_results(results_path):
    if not results_path.is_file():
        raise ValueError("results.xml was not produced -- likely a compile error")
    tree = ET.parse(str(results_path))
    outcomes = {}
    for testcase in tree.getroot().iter("testcase"):
        name = testcase.get("name")
        failure = testcase.find("failure") is not None or testcase.find("error") is not None
        outcomes[name] = not failure
    return outcomes


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="pwm-gen-eval-"))
    stage(workdir)

    outcomes = {}
    diagnostics = {}

    try:
        proc, results_path = run_simulation(workdir)
        test_outcomes = parse_results(results_path)
        for number, test_name in TEST_FOR.items():
            if test_name not in test_outcomes:
                outcomes[number] = 0
                diagnostics[number] = {"error": "test %r did not appear in results.xml" % test_name}
            elif test_outcomes[test_name]:
                outcomes[number] = 1
                diagnostics[number] = {"ok": True}
            else:
                outcomes[number] = 0
                diagnostics[number] = {"error": "%s failed; see simulator log" % test_name}
        if not any(outcomes.get(k) for k in outcomes) and proc.returncode != 0 and not test_outcomes:
            raise ValueError("simulation produced no test results: %s" % proc.stdout[-2000:])
    except ValueError as error:
        for k in ("1", "2", "3", "4", "5"):
            outcomes[k] = 0
            diagnostics[k] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "pwm-duty-sync",
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
