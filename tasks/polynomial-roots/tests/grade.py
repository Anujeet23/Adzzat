#!/usr/bin/env python3
"""Grades the polynomial-roots submission.

Five independent, weighted criteria, each checked against a polynomial
built from a known, exact set of roots, via optimal one-to-one matching
plus an independently computed residual -- never trusting anything the
submission itself claims beyond the returned list of complex numbers:

  1. well-separated real roots                       15%
  2. real coefficients, complex roots                 20%
  3. clustered near-degenerate roots                  25%
  4. an exact high-multiplicity root                  25%
  5. a batch of several polynomials in one run         15%
"""
import itertools
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
WEIGHTS = {"1": 15, "2": 20, "3": 25, "4": 25, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 30

FIXTURE_FOR = {
    "1": "separated_real.json",
    "2": "mixed_complex.json",
    "3": "clustered.json",
    "4": "high_multiplicity.json",
    "5": "mixed_batch.json",
}


def check_submission():
    if not (SUBMISSION / "rootfind" / "__init__.py").is_file():
        raise ValueError("Submitted rootfind package is missing")


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


def poly_eval(coeffs, z):
    result = 0j
    for c in coeffs:
        result = result * z + c
    return result


def poly_scale(coeffs, z):
    n = len(coeffs) - 1
    return sum(abs(c) * (abs(z) ** (n - i)) for i, c in enumerate(coeffs)) or 1.0


def best_match_distance(returned, true):
    n = len(true)
    if len(returned) != n:
        raise ValueError("expected %d roots, got %d" % (n, len(returned)))
    if n == 0:
        return 0.0
    if n <= 8:
        best = None
        for perm in itertools.permutations(range(n)):
            d = max(abs(returned[i] - true[perm[i]]) for i in range(n))
            if best is None or d < best:
                best = d
        return best
    remaining = list(range(n))
    worst = 0.0
    for r in returned:
        j = min(remaining, key=lambda k: abs(r - true[k]))
        remaining.remove(j)
        worst = max(worst, abs(r - true[j]))
    return worst


def check_one(coeffs, true_pairs, returned_pairs, match_tol, residual_rel_tol):
    true_roots = [complex(re, im) for re, im in true_pairs]
    returned = [complex(re, im) for re, im in returned_pairs]

    for r in returned:
        residual = abs(poly_eval(coeffs, r))
        scale = poly_scale(coeffs, r)
        if residual > 1e-8 + residual_rel_tol * scale:
            raise ValueError(
                "returned value %s has residual |p(r)|=%.3g, exceeding tolerance "
                "(scale=%.3g, rel_tol=%.3g)" % (r, residual, scale, residual_rel_tol)
            )

    dist = best_match_distance(returned, true_roots)
    if dist > match_tol:
        raise ValueError(
            "best one-to-one matching against the true roots has max distance %.3g, "
            "exceeding tolerance %.3g (true=%s, returned=%s)"
            % (dist, match_tol, true_roots, returned)
        )
    return {"max_match_distance": dist}


def criterion(runner, fixtures_dst, workdir, number):
    fname = FIXTURE_FOR[number]
    with open(HERE / "fixtures" / fname, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    result = run_fixture(runner, fixtures_dst / fname, workdir, "c" + number)
    if not result.get("ok"):
        raise ValueError("runner failed: %s" % result.get("error"))

    if "polynomials" in fixture:
        entries = fixture["polynomials"]
    else:
        entries = [fixture]

    outputs = result["results"]
    if len(outputs) != len(entries):
        raise ValueError("expected %d polynomial results, got %d" % (len(entries), len(outputs)))

    details = []
    for entry, output in zip(entries, outputs):
        details.append(
            check_one(
                entry["coeffs"],
                entry["roots"],
                output["roots"],
                fixture.get("match_tol", 1e-6),
                fixture.get("residual_rel_tol", 1e-6),
            )
        )
    return {"polynomials_checked": len(entries), "details": details}


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="poly-eval-"))
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
        "task_id": "polynomial-roots",
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
