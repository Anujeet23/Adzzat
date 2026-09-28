# Exception-safe resource pool

The agent makes a bounded resource pool exception-safe: a factory failure, an exception in caller code while holding a resource, or an explicitly broken resource must never permanently shrink the pool's capacity, double-issue a resource, or skip cleanup. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access. Pure in-memory logic -- no disk I/O, no subprocess crash injection needed. Agent and verifier each get two CPU cores and 2 GiB RAM; the agent has four hours and the verifier thirty minutes.

## Grading mechanism

The verifier never inspects source or reads the agent's transcript. A scripted, fixed sequence of pool operations -- `acquire`, `release`, `with pool.acquire() as h: ...` with and without an injected caller exception, `mark_broken()`, and a resource-factory configured to fail on an exact, pre-determined call -- is executed against the submission's actual `ResourcePool` object in an unprivileged subprocess, asserting after every single step that `outstanding + available == max_size` and that no two live handles ever wrap the same underlying resource. `destroy()` call counts and final `created_total` are checked exactly, not just "did it not crash."

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic correctness | 15% | acquire/release/exhaustion, no failures injected |
| Exception safety | 30% | Caller exceptions inside `with`, with and without `mark_broken()` |
| Broken-resource handling | 25% | `destroy()` called exactly once, capacity still reaches max_size |
| Factory-failure resilience | 20% | A factory failure must not permanently lose a slot |
| Mixed sequence | 10% | All of the above combined, checked by final invariants only |

All five are deterministic: no real threads, no timing, no blocking/waiting semantics at all (there is no `blocking` parameter in the API -- an exhausted pool always raises immediately, which sidesteps the flakiness that real concurrency would introduce). The harness reward is binary; the weighted score and per-criterion diagnostics are retained separately.

## Layout

- `instruction.md`: agent request (438 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the unsafe starter `pool` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: scripted-op runner, grader, and fixtures.

## Status

Fully validated end-to-end through real Docker containers (both images build clean; the oracle solution scores `reward=1`, 5/5, on the first run through the real, separate verifier container; the unsafe starter scores `0.15`, failing exactly the four bugs it has, with precise diagnostics; `reproduce.py` reproduces both starter bugs live). Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 (pass rate, step counts, score spread) required by the author brief, and the QC/QA script once it's provided.
