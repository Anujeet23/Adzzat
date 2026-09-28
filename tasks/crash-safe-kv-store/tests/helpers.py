"""Shared helpers for the crash-safe-kv-store grader."""
import json
import os
import subprocess


def simulate(ops, upto):
    """Logical key/value state after applying ops[:upto] (put/delete only; get/compact are no-ops)."""
    state = {}
    for op in ops[:upto]:
        kind = op["op"]
        if kind == "put":
            state[op["key"]] = op["value"]
        elif kind == "delete":
            state.pop(op["key"], None)
    return state


def clean_env(extra=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    if extra:
        env.update(extra)
    return env


def _maybe_drop_priv(kwargs, drop_priv):
    if drop_priv and os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() == 0:
        kwargs["user"] = 65534
        kwargs["group"] = 65534
        kwargs["extra_groups"] = []
    return kwargs


def run(cmd, timeout, cwd=None, drop_priv=True, env_extra=None):
    kwargs = dict(
        capture_output=True,
        timeout=timeout,
        cwd=cwd,
        env=clean_env(env_extra),
    )
    _maybe_drop_priv(kwargs, drop_priv)
    return subprocess.run(cmd, **kwargs)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def pick_representative(call_ids, cap):
    call_ids = sorted(set(call_ids))
    if len(call_ids) <= cap:
        return call_ids
    step = (len(call_ids) - 1) / (cap - 1)
    picked = []
    for i in range(cap):
        idx = round(i * step)
        picked.append(call_ids[idx])
    out = []
    for c in picked:
        if c not in out:
            out.append(c)
    return out


def op_call_ids(trace, op_index):
    return [entry["call_id"] for entry in trace if entry["op_index"] == op_index]
