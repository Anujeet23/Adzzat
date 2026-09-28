# Beam search

The agent fixes a beam search decoder that prunes candidates using a length-normalized score at every intermediate step (instead of raw cumulative log-probability, normalizing only at the very end) and breaks score ties non-deterministically. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no ML libraries -- `transition_logprobs` is given directly as a small, fully deterministic lookup table, so there's no real language model involved.

## Grading mechanism

`grade.py` contains its own from-scratch reference implementation of the exact algorithm specified in the contract (raw-score pruning during search, length-normalized final ranking, lexicographic tie-break at every selection step) and uses it as ground truth -- the submission's output must match it exactly: the same sequences, in the same order, with raw log-probabilities matching to floating-point tolerance. This is possible because the transition table is small and fully known, so there is exactly one correct answer for each fixture, not a fuzzy approximation.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic table | 20% | Baseline correctness |
| Premature normalization exposed | 25% | A short, immediately-completed sequence has the best final score but a worse per-step partial score |
| Second stress table | 20% | Same distinction, different transition table |
| Exact tie | 20% | Two candidates with identical score; only the lexicographic rule resolves it |
| Mixed batch | 15% | Three tables combining the above, in one run |

All five are exact-match, deterministic checks (no timing, no randomness) against an independently implemented reference.

## Layout

- `instruction.md`: agent request (407 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the premature-normalization starter `beamsearch` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: runner, grader (with its own independent reference beam search), and fixtures.

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, on the first run through the real, separate verifier container. The premature-normalization starter scores `0.4`, correctly failing the two dedicated normalization-timing fixtures and the batch that includes them, while passing the basic case and -- by the coincidence that its token-iteration order already matches lexicographic order for a single-position tie -- the dedicated tie-break fixture too (a real submission using a different iteration or beam-ordering strategy would not be so lucky, and the contract's tie-break rule is checked exactly regardless). `reproduce.py` reproduces the pruning bug live. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
