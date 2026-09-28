#!/usr/bin/env python3
"""Grades the scalar-autodiff submission.

Five independent, weighted criteria, each checked via central-difference
numerical differentiation of an independently, plainly-implemented mirror
of the same graph -- never trusting anything the submission's Value class
computes for the comparison itself:

  1. simple chain, every value used once            15%
  2. a value used by multiple operations (diamond)   30%
  3. graph built inside a Python loop                 20%
  4. relu/tanh/exp/log mixed with reuse                20%
  5. small mixed integration case, 11 leaves           15%
"""
import json
import math
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
WEIGHTS = {"1": 15, "2": 30, "3": 20, "4": 20, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 30
H = 1e-4
GRAD_TOL = 1e-3

FIXTURE_FOR = {
    "1": "chain.json",
    "2": "diamond.json",
    "3": "loop_sum.json",
    "4": "nonlinear.json",
    "5": "mixed_mlp.json",
}


def chain_float(leaves):
    x, w = leaves["x"], leaves["w"]
    return (x * w + 5) / 3 - 1


def diamond_float(leaves):
    x = leaves["x"]
    t = x * x
    u = x * t
    return t + u


def loop_sum_float(leaves):
    s = leaves["b"]
    for i in range(3):
        s = s + leaves["x%d" % i] * leaves["w%d" % i]
    return s


def nonlinear_float(leaves):
    x, y = leaves["x"], leaves["y"]
    a = math.tanh(x)
    b = math.exp(y)
    relu_a = a if a > 0 else 0.0
    c = a * b + relu_a
    return c * c


def mixed_mlp_float(leaves):
    x1, x2 = leaves["x1"], leaves["x2"]
    h1 = math.tanh(x1 * leaves["w11"] + x2 * leaves["w21"] + leaves["b1"])
    h2 = math.tanh(x1 * leaves["w12"] + x2 * leaves["w22"] + leaves["b2"])
    return h1 * leaves["wo1"] + h2 * leaves["wo2"] + leaves["bo"]


CASES_FLOAT = {
    "chain": chain_float,
    "diamond": diamond_float,
    "loop_sum": loop_sum_float,
    "nonlinear": nonlinear_float,
    "mixed_mlp": mixed_mlp_float,
}


def check_submission():
    if not (SUBMISSION / "autodiff" / "__init__.py").is_file():
        raise ValueError("Submitted autodiff package is missing")


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


def numeric_grad(fn, leaves, name):
    plus = dict(leaves)
    minus = dict(leaves)
    plus[name] = leaves[name] + H
    minus[name] = leaves[name] - H
    return (fn(plus) - fn(minus)) / (2 * H)


def criterion(runner, fixtures_dst, workdir, number):
    fname = FIXTURE_FOR[number]
    with open(HERE / "fixtures" / fname, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    case = fixture["case"]
    leaves = fixture["leaves"]

    result = run_fixture(runner, fixtures_dst / fname, workdir, "c" + number)
    if not result.get("ok"):
        raise ValueError("runner failed: %s" % result.get("error"))

    fn = CASES_FLOAT[case]
    reference_output = fn(leaves)
    if abs(result["output"] - reference_output) > 1e-6 + 1e-6 * abs(reference_output):
        raise ValueError(
            "forward output mismatch: got %.10g, expected %.10g" % (result["output"], reference_output)
        )

    details = {}
    for name in leaves:
        expected = numeric_grad(fn, leaves, name)
        got = result["grads"][name]
        scale = max(1.0, abs(expected))
        if abs(got - expected) > GRAD_TOL * scale:
            raise ValueError(
                "gradient mismatch for leaf %r: got %.6g, expected (central diff) %.6g" % (name, got, expected)
            )
        details[name] = {"got": got, "expected": expected}
    return details


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="autodiff-eval-"))
    os.chmod(workdir, 0o777)
    _, fixtures_dst = stage(workdir)
    runner = str(workdir / "stage" / "runner.py")

    outcomes = {}
    diagnostics = {}
    for number in ("1", "2", "3", "4", "5"):
        try:
            diagnostics[number] = criterion(runner, fixtures_dst, workdir, number)
            outcomes[number] = 1
        except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
            outcomes[number] = 0
            diagnostics[number] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "scalar-autodiff",
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
