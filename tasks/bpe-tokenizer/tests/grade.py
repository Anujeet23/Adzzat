#!/usr/bin/env python3
"""Grades the bpe-tokenizer submission.

Five independent, weighted criteria, each checked exactly against this
file's own from-scratch reference implementation of the algorithm
specified in TASK_CONTRACT.md -- never against the submission's own claims:

  1. basic training, no ties                          20%
  2. exact frequency tie during training               25%
  3. encode must respect merge priority, not L-to-R    25%
  4. repeated-character pair-count stress               15%
  5. integration: train + encode several words          15%
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
WEIGHTS = {"1": 20, "2": 25, "3": 25, "4": 15, "5": 15}
PYTHON = sys.executable
CALL_TIMEOUT = 30
END = "</w>"

FIXTURE_FOR = {
    "1": "basic.json",
    "2": "tie_break.json",
    "3": "encode_priority.json",
    "4": "repeated_char.json",
    "5": "integration.json",
}


def _word_symbols(word):
    return list(word) + [END]


def reference_train_bpe(word_freqs, num_merges):
    wsf = [(_word_symbols(w), f) for w, f in word_freqs.items()]
    merges = []
    for _ in range(num_merges):
        counts = {}
        for symbols, freq in wsf:
            for i in range(len(symbols) - 1):
                pair = (symbols[i], symbols[i + 1])
                counts[pair] = counts.get(pair, 0) + freq
        if not counts:
            break
        best_count = max(counts.values())
        if best_count <= 1:
            break
        best_pair = min(p for p, c in counts.items() if c == best_count)
        merges.append(best_pair)
        a, b = best_pair
        new_wsf = []
        for symbols, freq in wsf:
            out, i = [], 0
            while i < len(symbols):
                if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
                    out.append(a + b)
                    i += 2
                else:
                    out.append(symbols[i])
                    i += 1
            new_wsf.append((out, freq))
        wsf = new_wsf
    return merges


def reference_encode(word, merges):
    symbols = _word_symbols(word)
    priority = {pair: i for i, pair in enumerate(merges)}
    while True:
        best_rank, best_index = None, None
        for i in range(len(symbols) - 1):
            rank = priority.get((symbols[i], symbols[i + 1]))
            if rank is not None and (best_rank is None or rank < best_rank):
                best_rank, best_index = rank, i
        if best_index is None:
            break
        a, b = symbols[best_index], symbols[best_index + 1]
        symbols = symbols[:best_index] + [a + b] + symbols[best_index + 2:]
    return symbols


def check_submission():
    if not (SUBMISSION / "bpe" / "__init__.py").is_file():
        raise ValueError("Submitted bpe package is missing")


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


def criterion(runner, fixtures_dst, workdir, number):
    fname = FIXTURE_FOR[number]
    with open(HERE / "fixtures" / fname, "r", encoding="utf-8") as f:
        fixture = json.load(f)
    result = run_fixture(runner, fixtures_dst / fname, workdir, "c" + number)
    if not result.get("ok"):
        raise ValueError("runner failed: %s" % result.get("error"))

    kind = fixture["kind"]
    if kind == "train":
        expected = [list(p) for p in reference_train_bpe(fixture["word_freqs"], fixture["num_merges"])]
        if result["merges"] != expected:
            raise ValueError("merges mismatch: got %s, expected %s" % (result["merges"], expected))
        return {"n_merges": len(expected)}

    if kind == "encode":
        merges = [tuple(p) for p in fixture["merges"]]
        expected = reference_encode(fixture["word"], merges)
        if result["symbols"] != expected:
            raise ValueError("symbols mismatch: got %s, expected %s" % (result["symbols"], expected))
        return {"symbols": expected}

    if kind == "train_and_encode":
        expected_merges = [list(p) for p in reference_train_bpe(fixture["word_freqs"], fixture["num_merges"])]
        if result["merges"] != expected_merges:
            raise ValueError(
                "merges mismatch: got %s, expected %s" % (result["merges"], expected_merges)
            )
        merges_tuples = [tuple(p) for p in expected_merges]
        for w in fixture["encode_words"]:
            expected_symbols = reference_encode(w, merges_tuples)
            got_symbols = result["encoded"].get(w)
            if got_symbols != expected_symbols:
                raise ValueError(
                    "encode mismatch for %r: got %s, expected %s" % (w, got_symbols, expected_symbols)
                )
        return {"n_merges": len(expected_merges), "n_words": len(fixture["encode_words"])}

    raise ValueError("unknown fixture kind: " + kind)


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="bpe-eval-"))
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
        "task_id": "bpe-tokenizer",
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
