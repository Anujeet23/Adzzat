# BPE tokenizer

The agent fixes a byte-pair-encoding trainer/encoder that breaks frequency ties using whichever pair it happened to count first (not the required lexicographic rule), and encodes by a single left-to-right greedy pass instead of always applying the single highest-priority available merge. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md).

## Environment

Digest-pinned Python 3.12.11 Debian Bookworm base, no native dependencies, no network access, no ML/tokenization libraries -- this is a from-scratch implementation of the real GPT-2/RoBERTa-style BPE algorithm, not a wrapper around `tokenizers` or `sentencepiece`. Purely symbolic/string processing, no numerics at all -- a deliberately different mechanism class from this project's other ML/AI tasks (autodiff engine, beam search).

## Grading mechanism

`grade.py` contains its own from-scratch reference implementation of `train_bpe`/`encode` per the exact algorithm in the contract, and uses it as ground truth: the submission's merge list and encoded symbol sequences must match exactly, not approximately -- there is exactly one correct answer for each fixture, not a fuzzy approximation.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Basic training | 20% | No ties, baseline correctness |
| Exact frequency tie | 25% | Two pairs tied at the same count; lexicographic rule must decide |
| Priority-ordered encoding | 25% | A later-priority merge appears earlier in the string; must wait |
| Repeated-character stress | 15% | Correct pair-count recomputation for words like `"aaaa"` |
| Integration | 15% | Train on a larger corpus, then encode six words; merges and every encoding checked |

All five are exact-match, deterministic checks (no randomness, no timing) against an independently implemented reference.

## Layout

- `instruction.md`: agent request (403 words).
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: the tie-break/priority-order-buggy starter `bpe` package, `TASK_CONTRACT.md`, and `reproduce.py`.
- `solution/`: author-only reference implementation and installation script.
- `tests/`: runner, grader (with its own independent reference trainer/encoder), and fixtures.

## Status

Fully validated end-to-end through real Docker containers: both images build clean; the oracle solution scores `reward=1`, 5/5, on the first run through the real, separate verifier container. The buggy starter scores `0`, failing all five fixtures -- both bugs turned out to be pervasive enough (ties are common across 6-10 training steps on small corpora; the priority-order bug affects every encode call) to touch nearly every fixture, which is a legitimate outcome and doesn't affect the validity of the grading design. `reproduce.py` reproduces both bugs live on minimal, hand-checkable examples. Still outstanding: the 5-rollout evidence against Opus 5 / GPT-5.6 required by the author brief, and the QC/QA script once it's provided.
