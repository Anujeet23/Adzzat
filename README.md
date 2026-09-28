# Terminal-Bench-Style Task Suite — Adzzat Assessment

Ten Terminal-Bench-style tasks authored against the brief in `1 - Terminal-Bench Task Spec (Author Brief).docx`, matching its required domain mix.

| # | Task | Domain | Oracle | Broken starter |
|---|------|--------|:---:|:---:|
| 1 | [crash-safe-kv-store](tasks/crash-safe-kv-store) | Software engineering | 5/5 | 0.15 |
| 2 | [exception-safe-pool](tasks/exception-safe-pool) | Software engineering | 5/5 | 0.15 |
| 3 | [polynomial-roots](tasks/polynomial-roots) | Scientific computing | 5/5 | 0.5 |
| 4 | [symmetric-eigensolver](tasks/symmetric-eigensolver) | Scientific computing | 5/5 | 0.55 |
| 5 | [scalar-autodiff](tasks/scalar-autodiff) | ML / AI | 5/5 | 0.3 |
| 6 | [beam-search](tasks/beam-search) | ML / AI | 5/5 | 0.4 |
| 7 | [bpe-tokenizer](tasks/bpe-tokenizer) | ML / AI | 5/5 | 0 |
| 8 | [fast-matmul](tasks/fast-matmul) | Kernel optimization | 5/5 | 0.35 |
| 9 | [cache-blocked-transpose](tasks/cache-blocked-transpose) | Kernel optimization | 5/5 | 0.35 |
| 10 | [sync-fifo](tasks/sync-fifo) | RTL | 5/5 | 0.7 |

Every oracle solution scores a full 5/5 (`reward=1`) through the real, separate-container verifier — built and run with Docker, not simulated. Every starter is a genuinely broken but plausible implementation that fails a specific, well-motivated subset of criteria; each task includes a `reproduce.py` (or, for `sync-fifo`, a cocotb testbench) demonstrating the bug live. All grading is fully deterministic: no wall-clock timing anywhere, including the two kernel-optimization tasks, which use operation-counting and simulated-cache-miss instrumentation instead.

## Layout

Each task directory follows the same structure:

```
<task-name>/
  instruction.md       # agent-facing prompt (≤600 words)
  task.toml             # Harbor resource/config
  environment/          # agent's starting point (broken code + contract + reproduce script)
  solution/             # author-only oracle solution + solve.sh
  tests/                # verifier: grader, fixtures, Dockerfile
  README.md              # task-specific design notes and validation status
```

## Status

All ten task packages are complete and validated end-to-end through real Docker containers (build, oracle run, broken-starter run). **Outstanding before final submission**, per the brief's acceptance bars:

- **5-rollout evidence** against Opus 5 / GPT-5.6 (pass rate ≤2/5, bimodal score spread, 100+ agent steps per successful rollout) — requires Harbor/Terminal-Bench plus live model access.
- **QC/QA script** run — not yet received.

See each task's own `README.md` for full validation detail.
