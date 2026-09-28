"""Shared helpers for the bpe-tokenizer grader."""
import os
import subprocess


def clean_env(extra=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    if extra:
        env.update(extra)
    return env


def run(cmd, timeout, cwd=None, drop_priv=True, env_extra=None):
    kwargs = dict(capture_output=True, timeout=timeout, cwd=cwd, env=clean_env(env_extra))
    if drop_priv and os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() == 0:
        kwargs["user"] = 65534
        kwargs["group"] = 65534
        kwargs["extra_groups"] = []
    return subprocess.run(cmd, **kwargs)
