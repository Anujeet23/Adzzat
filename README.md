# Terminal-Bench-Style Task Suite — Adzzat Assessment

Twenty-five Terminal-Bench-style tasks: the first ten (rows 1-10) were authored against the Author Brief's required domain mix; the second batch (rows 11-25: Program Bench, RTL and Chip Design, five each) was added for the follow-up sample request.

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
| 11 | [lru-cache-with-ttl](tasks/lru-cache-with-ttl) | Program Bench | 5/5 | 0.15 |
| 12 | [token-bucket-rate-limiter](tasks/token-bucket-rate-limiter) | Program Bench | 5/5 | 0.15 |
| 13 | [lock-free-spsc-ring-buffer](tasks/lock-free-spsc-ring-buffer) | Program Bench | 5/5 | 0.15 |
| 14 | [incremental-topological-sort](tasks/incremental-topological-sort) | Program Bench | 5/5 | 0.15 |
| 15 | [streaming-json-parser](tasks/streaming-json-parser) | Program Bench | 5/5 | 0.15 |
| 16 | [programmable-modulus-counter](tasks/programmable-modulus-counter) | RTL | 5/5 | 0 |
| 17 | [uart-transmitter](tasks/uart-transmitter) | RTL | 5/5 | 0 |
| 18 | [spi-master](tasks/spi-master) | RTL | 5/5 | 0 |
| 19 | [pwm-duty-sync](tasks/pwm-duty-sync) | RTL | 5/5 | 0 |
| 20 | [debounce-edge-detector](tasks/debounce-edge-detector) | RTL | 5/5 | 0 |
| 21 | [round-robin-arbiter](tasks/round-robin-arbiter) | Chip Design | 5/5 | 0.15 |
| 22 | [direct-mapped-cache-controller](tasks/direct-mapped-cache-controller) | Chip Design | 5/5 | 0.4 |
| 23 | [pipeline-forwarding-unit](tasks/pipeline-forwarding-unit) | Chip Design | 5/5 | 0.45 |
| 24 | [axi-lite-register-slave](tasks/axi-lite-register-slave) | Chip Design | 5/5 | 0.3 |
| 25 | [memory-mapped-interrupt-controller](tasks/memory-mapped-interrupt-controller) | Chip Design | 5/5 | 0.3 |

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

All twenty-five task packages are complete and validated end-to-end through real Docker containers (build, oracle run, broken-starter run). **Outstanding before final submission**, per the brief's acceptance bars:

- **5-rollout evidence** against Opus 5 / GPT-5.6 (pass rate ≤2/5, bimodal score spread, 100+ agent steps per successful rollout) — requires Harbor/Terminal-Bench plus live model access; not run (see `qa/report.html`, criterion 2, for a free zero-cost proxy check using agentic subagents in place of paid rollouts, flagged there as a risk since it is not equivalent to real model evidence).
- **QC/QA script**, run using the runbook's own Appendix scripts (`eval_guide.md` rubric + `dq_audit.py`): 4/10 tasks flagged. Findings on 3 tasks were real grading-instrumentation bypasses (submission-controlled infrastructure files could self-report favorable stats instead of the harness measuring them) and a weak test fixture; all three have been fixed and re-validated in Docker — see `tasks/fast-matmul/README.md`, `tasks/cache-blocked-transpose/README.md`, and `tasks/beam-search/README.md`. Full merged results in `qa/report.html` and `qa/results.jsonl`.

See each task's own `README.md` for full validation detail.

### Second batch (tasks 11-25)

Built on branch `phase2-program-chip-rtl-samples`. All 15 were Docker-validated (oracle 5/5, naive starter fails the intended bug), then run through the same runbook QC/QA pass as the first ten (`qa/phase2/report.html`, `results.jsonl`): 7 of 15 were flagged. Real findings were fixed and re-validated (spec/test mismatches in `axi-lite-register-slave`, `programmable-modulus-counter`, `pwm-duty-sync`; missing coverage in `lru-cache-with-ttl`, `incremental-topological-sort`, `uart-transmitter`); the rest (thin fixtures, untested reset, results-file tampering by a hostile submission) are disclosed in each task's README. No grader measures anything through submission-supplied instrumentation, but the Python runners do share a process with the submission and read a result file from a scratch directory, so a deliberately hostile submission could forge it (same as the first-batch Python tasks). Rollout evidence against Opus 5 / GPT-5.6 was not run for either batch.
