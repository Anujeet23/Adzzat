#!/usr/bin/env python3
"""Grades the beam-search submission.

Five independent, weighted criteria, each checked exactly (sequences and
order must match; scores to floating-point tolerance) against this file's
own from-scratch reference implementation of the algorithm specified in
TASK_CONTRACT.md -- never against the submission's own claims:

  1. basic transition table                           20%
  2. premature normalization exposed                    25%
  3. second stress table                                 20%
  4. exact score tie, lexicographic tie-break required   20%
  5. batch of three tables in one run                    15%
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
WEIGHTS = {"1": 20, "2": 25, "3": 20, "4": 20, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 30

FIXTURE_FOR = {
    "1": "basic.json",
    "2": "length_normalization.json",
    "3": "breadth_stress.json",
    "4": "tie_break.json",
    "5": "mixed_batch.json",
}


def reference_beam_search(transition_logprobs, start_token, end_token, vocab_size, beam_width, max_length):
    beams = [([], 0.0, False)]
    for _ in range(max_length):
        if all(done for _, _, done in beams):
            break
        candidates = []
        for seq, score, done in beams:
            if done:
                candidates.append((seq, score, True))
                continue
            prev = seq[-1] if seq else start_token
            logprobs = transition_logprobs[prev]
            for tok in range(vocab_size):
                new_seq = seq + [tok]
                new_score = score + logprobs[tok]
                candidates.append((new_seq, new_score, tok == end_token))
        candidates.sort(key=lambda c: (-c[1], tuple(c[0])))
        beams = candidates[:beam_width]
    beams.sort(key=lambda c: (-(c[1] / len(c[0])), tuple(c[0])))
    return [(seq, score) for seq, score, _ in beams]


def check_submission():
    if not (SUBMISSION / "beamsearch" / "__init__.py").is_file():
        raise ValueError("Submitted beamsearch package is missing")


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


def check_one(case, output):
    table = {int(k): v for k, v in case["transition_logprobs"].items()}
    expected = reference_beam_search(
        table, case["start_token"], case["end_token"], case["vocab_size"], case["beam_width"], case["max_length"]
    )
    expected_seqs = [seq for seq, _ in expected]
    got_seqs = [entry["sequence"] for entry in output]
    if got_seqs != expected_seqs:
        raise ValueError(
            "sequence mismatch: got %s, expected %s" % (got_seqs, expected_seqs)
        )
    for (_, exp_score), entry in zip(expected, output):
        if abs(entry["raw_logprob"] - exp_score) > 1e-6 + 1e-6 * abs(exp_score):
            raise ValueError(
                "raw_logprob mismatch for %s: got %.6g, expected %.6g"
                % (entry["sequence"], entry["raw_logprob"], exp_score)
            )
    return {"n_sequences": len(expected_seqs)}


def criterion(runner, fixtures_dst, workdir, number):
    fname = FIXTURE_FOR[number]
    with open(HERE / "fixtures" / fname, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    result = run_fixture(runner, fixtures_dst / fname, workdir, "c" + number)
    if not result.get("ok"):
        raise ValueError("runner failed: %s" % result.get("error"))

    cases = fixture["cases"] if "cases" in fixture else [fixture]
    outputs = result["results"]
    if len(outputs) != len(cases):
        raise ValueError("expected %d case results, got %d" % (len(cases), len(outputs)))

    details = [check_one(case, output) for case, output in zip(cases, outputs)]
    return {"cases_checked": len(cases), "details": details}


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="beam-eval-"))
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
        "task_id": "beam-search",
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
