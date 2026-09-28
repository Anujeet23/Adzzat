#!/usr/bin/env python3
"""Grades the symmetric-eigensolver submission.

Five independent, weighted criteria, each checked against a matrix built
from a known eigendecomposition, via optimal eigenvalue matching plus
independently computed residual and orthogonality checks:

  1. well-separated eigenvalues                       15%
  2. clustered eigenvalues 0.001 apart                 25%
  3. an exactly repeated eigenvalue                    25%
  4. negative dominant eigenvalue                       15%
  5. a batch of several matrices in one run             20%
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
WEIGHTS = {"1": 15, "2": 25, "3": 25, "4": 15, "5": 20}
PYTHON = sys.executable
CALL_TIMEOUT = 30

FIXTURE_FOR = {
    "1": "separated.json",
    "2": "clustered.json",
    "3": "repeated.json",
    "4": "negative_dominant.json",
    "5": "mixed_batch.json",
}


def check_submission():
    if not (SUBMISSION / "eigensolve" / "__init__.py").is_file():
        raise ValueError("Submitted eigensolve package is missing")


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


def matvec(matrix, v):
    n = len(matrix)
    return [sum(matrix[i][k] * v[k] for k in range(n)) for i in range(n)]


def best_match_distance(returned, true):
    n = len(true)
    if len(returned) != n:
        raise ValueError("expected %d eigenvalues, got %d" % (n, len(returned)))
    best = None
    for perm in itertools.permutations(range(n)):
        d = max(abs(returned[i] - true[perm[i]]) for i in range(n))
        if best is None or d < best:
            best = d
    return best


def check_one(matrix, true_eigenvalues, values, vectors, value_tol, residual_tol):
    n = len(matrix)
    if len(values) != n or len(vectors) != n:
        raise ValueError("expected %d eigenvalues/eigenvectors, got %d/%d" % (n, len(values), len(vectors)))

    dist = best_match_distance(values, true_eigenvalues)
    if dist > value_tol:
        raise ValueError(
            "best one-to-one matching of eigenvalues has max distance %.3g, "
            "exceeding tolerance %.3g (true=%s, returned=%s)" % (dist, value_tol, true_eigenvalues, values)
        )

    matrix_scale = max(abs(x) for row in matrix for x in row) or 1.0

    for j in range(n):
        v = vectors[j]
        if len(v) != n:
            raise ValueError("eigenvector %d has wrong length %d" % (j, len(v)))
        norm = sum(x * x for x in v) ** 0.5
        if abs(norm - 1.0) > 1e-6:
            raise ValueError("eigenvector %d is not unit norm: |v|=%.6g" % (j, norm))
        Av = matvec(matrix, v)
        residual = max(abs(Av[i] - values[j] * v[i]) for i in range(n))
        if residual > 1e-9 + residual_tol * matrix_scale:
            raise ValueError(
                "eigenvector %d residual |Av - lambda*v|=%.3g exceeds tolerance "
                "(scale=%.3g, rel_tol=%.3g)" % (j, residual, matrix_scale, residual_tol)
            )

    for a in range(n):
        for b in range(a + 1, n):
            dot = sum(vectors[a][i] * vectors[b][i] for i in range(n))
            if abs(dot) > 1e-6 + residual_tol:
                raise ValueError(
                    "eigenvectors %d and %d are not orthogonal: dot=%.3g" % (a, b, dot)
                )

    return {"max_value_match_distance": dist}


def criterion(runner, fixtures_dst, workdir, number):
    fname = FIXTURE_FOR[number]
    with open(HERE / "fixtures" / fname, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    result = run_fixture(runner, fixtures_dst / fname, workdir, "c" + number)
    if not result.get("ok"):
        raise ValueError("runner failed: %s" % result.get("error"))

    if "matrices" in fixture:
        entries = fixture["matrices"]
    else:
        entries = [fixture]

    outputs = result["results"]
    if len(outputs) != len(entries):
        raise ValueError("expected %d matrix results, got %d" % (len(entries), len(outputs)))

    details = []
    for entry, output in zip(entries, outputs):
        details.append(
            check_one(
                entry["matrix"],
                entry["eigenvalues"],
                output["eigenvalues"],
                output["eigenvectors"],
                fixture.get("value_tol", 1e-6),
                fixture.get("residual_tol", 1e-6),
            )
        )
    return {"matrices_checked": len(entries), "details": details}


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="eig-eval-"))
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
        "task_id": "symmetric-eigensolver",
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
