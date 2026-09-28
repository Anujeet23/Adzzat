#!/usr/bin/env python3
"""Grades the crash-safe-kv-store submission.

Five independent, weighted criteria, each exercised with real subprocess
kills and real on-disk state:

  1. basic functional correctness (no crashes)                      15%
  2. durability of put/delete under a kill at many points            25%
  3. crash safety of compact() under a kill at every call it makes   30%
  4. reader isolation during concurrent compaction                   20%
  5. durability-relevant work is actually routed through iolayer     10%
"""
import json
import os
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import op_call_ids, pick_representative, read_json, run, simulate  # noqa: E402

HERE = Path(__file__).resolve().parent
LOGS = Path(os.environ.get("KV_GRADE_LOGS_DIR", "/logs/verifier"))
SUBMISSION = Path(os.environ.get("KV_GRADE_SUBMISSION_DIR", "/app/submission"))
WEIGHTS = {"1": 15, "2": 25, "3": 30, "4": 20, "5": 10}
PYTHON = sys.executable
CALL_TIMEOUT = 60
MAX_CRASH_POINTS_PER_OP = 3
MAX_COMPACT_POINTS = 8

# Set by stage_scripts(): /tests is chmod 700 (root-only), but the worker and
# recovery scripts are invoked as unprivileged uid 65534, so they -- and the
# fixtures they read -- must be staged to a world-readable+traversable copy
# first, the same way the sample task's grade.py stages probe.py.
WORKER = None
RECOVERY = None
FIXTURES_DIR = None


def new_workdir():
    base = Path(tempfile.mkdtemp(prefix="kv-eval-"))
    os.chmod(base, 0o777)
    return base


def stage_scripts(workdir):
    global WORKER, RECOVERY, FIXTURES_DIR
    stage = workdir / "stage"
    stage.mkdir(mode=0o755)
    for name in ("crash_worker.py", "recovery_check.py", "helpers.py"):
        dst = stage / name
        shutil.copyfile(HERE / name, dst)
        os.chmod(dst, 0o644)
    fixtures_dst = stage / "fixtures"
    fixtures_dst.mkdir(mode=0o755)
    for fixture in (HERE / "fixtures").glob("*.json"):
        dst = fixtures_dst / fixture.name
        shutil.copyfile(fixture, dst)
        os.chmod(dst, 0o644)
    WORKER = str(stage / "crash_worker.py")
    RECOVERY = str(stage / "recovery_check.py")
    FIXTURES_DIR = fixtures_dst


def db_path(workdir, tag):
    d = workdir / tag
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o777)
    return str(d / "store.db")


def check_submission():
    if not (SUBMISSION / "kvstore" / "__init__.py").is_file():
        raise ValueError("Submitted kvstore package is missing")


def dry_run(ops_path, workdir, tag):
    check_submission()
    db = db_path(workdir, tag)
    trace_out = str(workdir / (tag + "-trace.json"))
    cmd = [PYTHON, WORKER, "--db", db, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path),
           "--trace-out", trace_out]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode != 0:
        raise ValueError(
            "dry run of %s failed (exit %s): %s" % (tag, proc.returncode, proc.stderr[-2000:])
        )
    trace = read_json(trace_out)
    return trace, db


def crash_scenario(ops_path, workdir, tag, call_id, probe_key):
    check_submission()
    scenario_tag = "%s-crash-%d" % (tag, call_id)
    db = db_path(workdir, scenario_tag)
    trace_out = str(workdir / (scenario_tag + "-trace.json"))
    cmd = [
        PYTHON, WORKER, "--db", db, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path),
        "--trace-out", trace_out, "--crash-after", str(call_id), "--partial-seed", str(call_id),
    ]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode not in (-9, 137, 0):
        raise ValueError(
            "unexpected crash-worker exit %s for call %s: %s"
            % (proc.returncode, call_id, proc.stderr[-2000:])
        )
    recovery_out = str(workdir / (scenario_tag + "-recovery.json"))
    cmd = [
        PYTHON, RECOVERY, "--db", db, "--pkgdir", str(SUBMISSION), "--out", recovery_out,
        "--probe-key", probe_key, "--probe-value", "probe-value-%d" % call_id,
    ]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    return read_json(recovery_out)


def pause_scenario(ops_path, workdir, tag, call_id):
    check_submission()
    scenario_tag = "%s-pause-%d" % (tag, call_id)
    db = db_path(workdir, scenario_tag)
    trace_out = str(workdir / (scenario_tag + "-ptrace.json"))
    pause_out = str(workdir / (scenario_tag + "-pause.json"))
    cmd = [
        PYTHON, WORKER, "--db", db, "--pkgdir", str(SUBMISSION), "--ops", str(ops_path),
        "--trace-out", trace_out, "--pause-after", str(call_id), "--pause-out", pause_out,
        "--recovery-script", RECOVERY,
    ]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    if proc.returncode != 0:
        raise ValueError(
            "pause run failed for call %s (exit %s): %s"
            % (call_id, proc.returncode, proc.stderr[-2000:])
        )
    if not os.path.isfile(pause_out):
        raise ValueError("no paused-reader output was produced for call %s" % call_id)
    return read_json(pause_out)


def states_match(items, expected):
    return items == expected


def criterion_1(ops, ops_path, workdir):
    trace, db = dry_run(ops_path, workdir, "basic")
    recovery_out = str(workdir / "basic-final.json")
    cmd = [PYTHON, RECOVERY, "--db", db, "--pkgdir", str(SUBMISSION), "--out", recovery_out]
    proc = run(cmd, timeout=CALL_TIMEOUT)
    result = read_json(recovery_out)
    expected = simulate(ops, len(ops))
    if not result.get("ok"):
        raise ValueError("basic recovery_check failed: %s" % result.get("error"))
    if not states_match(result["items"], expected):
        raise ValueError(
            "basic state mismatch: got %s expected %s" % (result["items"], expected)
        )
    return trace, {"expected": expected, "actual": result["items"]}


def criterion_2(ops, ops_path, workdir, trace_basic_unused):
    trace, _ = dry_run(ops_path, workdir, "durability")
    put_del_indices = [i for i, op in enumerate(ops) if op["op"] in ("put", "delete")]
    details = {}
    for op_index in put_del_indices:
        ids = op_call_ids(trace, op_index)
        if not ids:
            raise ValueError(
                "op %d (%s) made no iolayer calls at all; writes must go through iolayer"
                % (op_index, ops[op_index]["op"])
            )
        picked = pick_representative(ids, MAX_CRASH_POINTS_PER_OP)
        before = simulate(ops, op_index)
        after = simulate(ops, op_index + 1)
        for call_id in picked:
            probe_key = "__probe_dur_%d_%d__" % (op_index, call_id)
            result = crash_scenario(ops_path, workdir, "durability", call_id, probe_key)
            if not result.get("ok"):
                raise ValueError(
                    "recovery failed after crash at call %d (op %d): %s"
                    % (call_id, op_index, result.get("error"))
                )
            items = result["items"]
            if items != before and items != after:
                raise ValueError(
                    "crash at call %d (op %d, %s) left state %s; expected either %s or %s"
                    % (call_id, op_index, ops[op_index]["op"], items, before, after)
                )
            if not result.get("probe_roundtrip"):
                raise ValueError(
                    "after crash at call %d (op %d), a fresh put/reopen no longer round-trips "
                    "-- likely a torn write that was never truncated on recovery" % (call_id, op_index)
                )
            details["call_%d" % call_id] = "ok"
    return details


def criterion_3(ops, ops_path, workdir, compact_op_index):
    trace, _ = dry_run(ops_path, workdir, "compaction")
    ids = op_call_ids(trace, compact_op_index)
    if not ids:
        raise ValueError("compact() made no iolayer calls at all")
    picked = pick_representative(ids, MAX_COMPACT_POINTS)
    before = simulate(ops, compact_op_index)
    details = {}
    for call_id in picked:
        probe_key = "__probe_compact_%d__" % call_id
        result = crash_scenario(ops_path, workdir, "compaction", call_id, probe_key)
        if not result.get("ok"):
            raise ValueError(
                "recovery failed after crash at call %d during compact(): %s"
                % (call_id, result.get("error"))
            )
        if result["items"] != before:
            raise ValueError(
                "crash at call %d during compact() changed logical state: got %s expected %s"
                % (call_id, result["items"], before)
            )
        if not result.get("probe_roundtrip"):
            raise ValueError(
                "after crash at call %d during compact(), store is no longer writable" % call_id
            )
        details["call_%d" % call_id] = "ok"
    return details, picked, trace


def criterion_4(ops, ops_path, workdir, compact_op_index, picked_calls):
    if not picked_calls:
        raise ValueError("compact() made no iolayer calls at all; nothing to pause on and verify")
    before = simulate(ops, compact_op_index)
    details = {}
    for call_id in picked_calls:
        result = pause_scenario(ops_path, workdir, "reader", call_id)
        if not result.get("ok"):
            raise ValueError(
                "concurrent reader raised while paused at call %d during compact(): %s"
                % (call_id, result.get("error"))
            )
        if result["items"] != before:
            raise ValueError(
                "concurrent reader paused at call %d during compact() saw mixed/partial state: "
                "got %s expected %s" % (call_id, result["items"], before)
            )
        details["call_%d" % call_id] = "ok"
    return details


def criterion_5(trace_basic, ops):
    missing = []
    for i, op in enumerate(ops):
        ids = op_call_ids(trace_basic, i)
        fns = {entry["fn"] for entry in trace_basic if entry["op_index"] == i}
        if op["op"] in ("put", "delete"):
            if not (fns & {"pwrite_all", "fsync"}):
                missing.append("op %d (%s): no pwrite_all/fsync call" % (i, op["op"]))
        elif op["op"] == "compact":
            if "atomic_replace" not in fns:
                missing.append("op %d (compact): no atomic_replace call" % i)
            if "fsync_dir" not in fns:
                missing.append("op %d (compact): no fsync_dir call" % i)
            if not (fns & {"pwrite_all", "fsync"}):
                missing.append("op %d (compact): no pwrite_all/fsync call for the tmp file" % i)
    if missing:
        raise ValueError("contract-compliance gaps: " + "; ".join(missing))
    return {"checked_ops": len(ops)}


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    workdir = new_workdir()
    stage_scripts(workdir)
    outcomes = {}
    diagnostics = {}

    basic_ops = read_json(HERE / "fixtures" / "basic.json")["ops"]
    basic_path = FIXTURES_DIR / "basic.json"
    durability_ops = read_json(HERE / "fixtures" / "durability.json")["ops"]
    durability_path = FIXTURES_DIR / "durability.json"
    compaction_fixture = read_json(HERE / "fixtures" / "compaction.json")
    compaction_ops = compaction_fixture["ops"]
    compaction_path = FIXTURES_DIR / "compaction.json"
    compact_op_index = compaction_fixture["compact_op_index"]

    trace_basic = None
    try:
        trace_basic, diag = criterion_1(basic_ops, basic_path, workdir)
        outcomes["1"] = 1
        diagnostics["1"] = diag
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        outcomes["1"] = 0
        diagnostics["1"] = {"error": str(error)}

    try:
        diagnostics["2"] = criterion_2(durability_ops, durability_path, workdir, trace_basic)
        outcomes["2"] = 1
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        outcomes["2"] = 0
        diagnostics["2"] = {"error": str(error)}

    picked_calls = []
    try:
        diag3, picked_calls, _ = criterion_3(compaction_ops, compaction_path, workdir, compact_op_index)
        outcomes["3"] = 1
        diagnostics["3"] = diag3
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        outcomes["3"] = 0
        diagnostics["3"] = {"error": str(error)}

    try:
        if not picked_calls:
            trace, _ = dry_run(compaction_path, workdir, "compaction")
            picked_calls = pick_representative(op_call_ids(trace, compact_op_index), MAX_COMPACT_POINTS)
        diagnostics["4"] = criterion_4(compaction_ops, compaction_path, workdir, compact_op_index, picked_calls)
        outcomes["4"] = 1
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        outcomes["4"] = 0
        diagnostics["4"] = {"error": str(error)}

    try:
        if trace_basic is None:
            trace_basic, _ = dry_run(basic_path, workdir, "basic")
        diagnostics["5"] = criterion_5(trace_basic, basic_ops)
        outcomes["5"] = 1
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        outcomes["5"] = 0
        diagnostics["5"] = {"error": str(error)}

    shutil.rmtree(workdir, ignore_errors=True)

    reward = int(all(outcomes.values()))
    report = {
        "task_id": "crash-safe-kv-store",
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
